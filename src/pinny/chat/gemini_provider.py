import logging
from collections.abc import AsyncIterator
from typing import Any

import httpx
from google import genai
from google.genai import errors, types

from pinny.chat.errors import (
    ProviderAuthenticationError,
    ProviderConfigurationError,
    ProviderError,
    ProviderInvalidRequestError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from pinny.chat.types import ChatMessage, GenerationResult, StreamItem, TextDelta
from pinny.core.config import Settings

logger = logging.getLogger(__name__)


class GeminiChatModel:
    def __init__(self, settings: Settings, client: Any | None = None) -> None:
        if settings.gemini_api_key is None or not settings.gemini_api_key.get_secret_value():
            raise ProviderConfigurationError("Gemini API key is not configured")
        self._client = (
            client
            or genai.Client(
                api_key=settings.gemini_api_key.get_secret_value(),
                http_options=types.HttpOptions(timeout=int(settings.gemini_timeout * 1000)),
            ).aio
        )
        self._model = settings.gemini_model
        self._max_output_tokens = settings.chat_max_output_tokens

    async def stream(self, messages: list[ChatMessage], user_id: str) -> AsyncIterator[StreamItem]:
        del user_id  # The neutral contract permits providers to ignore this identifier.
        system_instruction, contents = self._map_messages(messages)
        stream = None
        yielded_text = False
        terminal_reason: str | None = None
        input_tokens: int | None = None
        output_tokens: int | None = None
        try:
            stream = await self._client.models.generate_content_stream(
                model=self._model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    max_output_tokens=self._max_output_tokens,
                ),
            )
            async for chunk in stream:
                text = self._safe_text(chunk)
                if text:
                    yielded_text = True
                    yield TextDelta(text)
                terminal_reason = self._finish_reason(chunk) or terminal_reason
                usage = getattr(chunk, "usage_metadata", None)
                if usage is not None:
                    input_tokens = getattr(usage, "prompt_token_count", input_tokens)
                    output_tokens = getattr(usage, "candidates_token_count", output_tokens)
            unsuccessful_reason = terminal_reason and terminal_reason != "STOP"
            if not yielded_text or unsuccessful_reason:
                raise ProviderError("Gemini generation did not complete")
            yield GenerationResult(
                provider="gemini",
                model=self._model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
        except TimeoutError as exc:
            self._log_failure(exc)
            raise ProviderTimeoutError from exc
        except errors.APIError as exc:
            self._log_failure(exc)
            code = getattr(exc, "code", None)
            if code in {408, 504}:
                raise ProviderTimeoutError from exc
            if code in {401, 403}:
                raise ProviderAuthenticationError from exc
            if code == 429:
                raise ProviderRateLimitError from exc
            if code in {400, 404, 422}:
                raise ProviderInvalidRequestError from exc
            if code is not None and code >= 500:
                raise ProviderUnavailableError from exc
            raise ProviderError from exc
        except httpx.TimeoutException as exc:
            self._log_failure(exc)
            raise ProviderTimeoutError from exc
        except httpx.HTTPError as exc:
            self._log_failure(exc)
            raise ProviderUnavailableError from exc
        except ProviderError:
            raise
        except Exception as exc:
            self._log_failure(exc)
            raise ProviderError from exc
        finally:
            if stream is not None:
                close = getattr(stream, "aclose", None)
                if close is not None:
                    await close()

    @staticmethod
    def _map_messages(messages: list[ChatMessage]) -> tuple[str | None, list[types.Content]]:
        system_parts: list[str] = []
        contents: list[types.Content] = []
        for message in messages:
            if message.role == "system":
                system_parts.append(message.content)
                continue
            role = "model" if message.role == "assistant" else "user"
            contents.append(
                types.Content(role=role, parts=[types.Part.from_text(text=message.content)])
            )
        return "\n\n".join(system_parts) or None, contents

    @staticmethod
    def _safe_text(chunk: Any) -> str:
        try:
            return chunk.text or ""
        except (AttributeError, ValueError):
            return ""

    @staticmethod
    def _finish_reason(chunk: Any) -> str | None:
        candidates = getattr(chunk, "candidates", None) or []
        if not candidates:
            return None
        reason = getattr(candidates[0], "finish_reason", None)
        return getattr(reason, "name", None) or (str(reason) if reason else None)

    @staticmethod
    def _log_failure(exc: Exception) -> None:
        logger.warning(
            "Gemini request failed",
            extra={"context": {"provider": "gemini", "error_type": type(exc).__name__}},
        )
