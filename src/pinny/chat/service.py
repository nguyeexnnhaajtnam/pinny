import asyncio
from collections.abc import AsyncIterator
from dataclasses import replace
from time import perf_counter
from uuid import UUID

from pinny.chat.context import ConversationContextBuilder
from pinny.chat.errors import ContextLimitError, LLMProviderError, ProviderTimeoutError
from pinny.chat.ports import ChatModel, ChatRepository, RuntimeContextProvider
from pinny.chat.prompt import PromptBuilder
from pinny.chat.types import (
    ChatEvent,
    GenerationMetadata,
    GenerationResult,
    PreparedChat,
    TextDelta,
)


class ChatService:
    def __init__(
        self,
        repository: ChatRepository,
        model: ChatModel,
        max_context_characters: int,
        runtime_context_provider: RuntimeContextProvider,
        context_builder: ConversationContextBuilder,
        prompt_builder: PromptBuilder,
        generation_timeout: float,
        retry_attempts: int,
        retry_delay_seconds: float,
    ) -> None:
        self._repository = repository
        self._model = model
        self._max_context_characters = max_context_characters
        self._runtime_context_provider = runtime_context_provider
        self._context_builder = context_builder
        self._prompt_builder = prompt_builder
        self._generation_timeout = generation_timeout
        self._retry_attempts = retry_attempts
        self._retry_delay_seconds = retry_delay_seconds

    async def prepare(
        self, user_id: str, message: str, conversation_id: UUID | None
    ) -> PreparedChat:
        prepared = await self._repository.prepare(user_id, message, conversation_id)
        context_messages = self._context_builder.build(
            prepared.history, prepared.current_user_message
        )
        if sum(len(item.content) for item in context_messages) > self._max_context_characters:
            await self._repository.terminate(prepared.assistant_message_id, "failed")
            raise ContextLimitError
        runtime_context = await self._runtime_context_provider.get_runtime_context()
        return replace(prepared, history=context_messages[:-1], runtime_context=runtime_context)

    async def stream(self, prepared: PreparedChat, user_id: str) -> AsyncIterator[ChatEvent]:
        yield ChatEvent(
            event="conversation",
            data={
                "conversation_id": str(prepared.conversation_id),
                "message_id": str(prepared.user_message_id),
            },
        )
        if prepared.runtime_context is None:
            raise RuntimeError("prepared chat is missing runtime context")
        messages = self._prompt_builder.build(
            prepared.runtime_context, prepared.history, prepared.current_user_message
        )
        chunks: list[str] = []
        result: GenerationResult | None = None
        started = perf_counter()
        await self._repository.mark_streaming(prepared.assistant_message_id)
        try:
            for attempt in range(1, self._retry_attempts + 1):
                try:
                    async with asyncio.timeout(self._generation_timeout):
                        provider_stream = self._model.stream(messages, user_id)
                        try:
                            async for item in provider_stream:
                                if isinstance(item, TextDelta):
                                    chunks.append(item.text)
                                    yield ChatEvent(
                                        event="delta",
                                        data={
                                            "conversation_id": str(prepared.conversation_id),
                                            "message_id": str(prepared.assistant_message_id),
                                            "content": item.text,
                                        },
                                    )
                                elif isinstance(item, GenerationResult):
                                    result = item
                        finally:
                            close = getattr(provider_stream, "aclose", None)
                            if close is not None:
                                await close()
                    if result is None:
                        raise LLMProviderError("provider stream omitted terminal result")
                    break
                except TimeoutError as exc:
                    error = ProviderTimeoutError("provider generation timed out")
                    if chunks or attempt >= self._retry_attempts:
                        raise error from exc
                except LLMProviderError as exc:
                    if chunks or not exc.retryable or attempt >= self._retry_attempts:
                        raise
                if self._retry_delay_seconds:
                    await asyncio.sleep(self._retry_delay_seconds)

            latency_ms = max(0, round((perf_counter() - started) * 1000))
            metadata = GenerationMetadata(
                provider=result.provider,
                model=result.model,
                latency_ms=latency_ms,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
            )
            await self._repository.complete(prepared, "".join(chunks), metadata)
        except asyncio.CancelledError:
            latency_ms = max(0, round((perf_counter() - started) * 1000))
            await asyncio.shield(
                self._repository.terminate(
                    prepared.assistant_message_id,
                    "cancelled",
                    GenerationMetadata(None, None, latency_ms),
                )
            )
            raise
        except Exception as exc:
            latency_ms = max(0, round((perf_counter() - started) * 1000))
            await asyncio.shield(
                self._repository.terminate(
                    prepared.assistant_message_id,
                    "failed",
                    GenerationMetadata(None, None, latency_ms),
                )
            )
            code = exc.code if isinstance(exc, LLMProviderError) else "generation_failed"
            yield ChatEvent(
                event="error",
                data={
                    "conversation_id": str(prepared.conversation_id),
                    "message_id": str(prepared.assistant_message_id),
                    "code": code,
                    "message": "Assistant generation failed",
                },
            )
            return
        yield ChatEvent(
            event="completed",
            data={
                "conversation_id": str(prepared.conversation_id),
                "message_id": str(prepared.assistant_message_id),
            },
        )

    async def interrupt(self, prepared: PreparedChat) -> None:
        await asyncio.shield(self._repository.terminate(prepared.assistant_message_id, "cancelled"))
