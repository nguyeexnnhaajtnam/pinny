import asyncio
from collections.abc import AsyncIterator
from uuid import UUID

from pinny.chat.errors import ContextLimitError, ProviderError
from pinny.chat.ports import ChatModel, ChatRepository
from pinny.chat.prompt import with_system_prompt
from pinny.chat.types import ChatEvent, PreparedChat


class ChatService:
    def __init__(
        self, repository: ChatRepository, model: ChatModel, max_context_characters: int
    ) -> None:
        self._repository = repository
        self._model = model
        self._max_context_characters = max_context_characters

    async def prepare(
        self, user_id: str, message: str, conversation_id: UUID | None
    ) -> PreparedChat:
        prepared = await self._repository.prepare(user_id, message, conversation_id)
        if sum(len(item.content) for item in prepared.history) > self._max_context_characters:
            await self._repository.fail(prepared.assistant_message_id, "failed")
            raise ContextLimitError
        return prepared

    async def stream(self, prepared: PreparedChat, user_id: str) -> AsyncIterator[ChatEvent]:
        yield ChatEvent(
            event="conversation",
            data={
                "conversation_id": str(prepared.conversation_id),
                "message_id": str(prepared.user_message_id),
            },
        )
        chunks: list[str] = []
        try:
            async for delta in self._model.stream(with_system_prompt(prepared.history), user_id):
                chunks.append(delta)
                yield ChatEvent(
                    event="delta",
                    data={"conversation_id": str(prepared.conversation_id), "content": delta},
                )
            await self._repository.complete(prepared, "".join(chunks))
        except asyncio.CancelledError:
            await asyncio.shield(
                self._repository.fail(prepared.assistant_message_id, "interrupted")
            )
            raise
        except Exception as exc:
            await asyncio.shield(self._repository.fail(prepared.assistant_message_id, "failed"))
            code = exc.code if isinstance(exc, ProviderError) else "generation_failed"
            yield ChatEvent(
                event="error",
                data={
                    "conversation_id": str(prepared.conversation_id),
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
        await asyncio.shield(self._repository.fail(prepared.assistant_message_id, "interrupted"))
