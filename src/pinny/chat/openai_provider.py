import logging
from collections.abc import AsyncIterator
from hashlib import sha256

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    RateLimitError,
)

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


class OpenAIChatModel:
    def __init__(self, settings: Settings, client: AsyncOpenAI | None = None) -> None:
        if settings.openai_api_key is None or not settings.openai_api_key.get_secret_value():
            raise ProviderConfigurationError("OpenAI API key is not configured")
        self._client = client or AsyncOpenAI(
            api_key=settings.openai_api_key.get_secret_value(), timeout=settings.openai_timeout
        )
        self._model = settings.openai_model
        self._max_output_tokens = settings.chat_max_output_tokens

    async def stream(self, messages: list[ChatMessage], user_id: str) -> AsyncIterator[StreamItem]:
        stream = None
        completed = False
        yielded_text = False
        try:
            stream = await self._client.responses.create(
                model=self._model,
                input=[{"role": item.role, "content": item.content} for item in messages],
                max_output_tokens=self._max_output_tokens,
                safety_identifier=sha256(user_id.encode()).hexdigest(),
                store=False,
                stream=True,
            )
            result: GenerationResult | None = None
            async for event in stream:
                if event.type == "response.output_text.delta":
                    if event.delta:
                        yielded_text = True
                        yield TextDelta(event.delta)
                elif event.type == "response.completed":
                    completed = True
                    response = getattr(event, "response", None)
                    usage = getattr(response, "usage", None)
                    result = GenerationResult(
                        provider="openai",
                        model=getattr(response, "model", None) or self._model,
                        input_tokens=getattr(usage, "input_tokens", None),
                        output_tokens=getattr(usage, "output_tokens", None),
                    )
                elif event.type in {"response.failed", "response.incomplete", "error"}:
                    raise ProviderError("OpenAI generation did not complete")
            if not completed or not yielded_text:
                raise ProviderError("OpenAI generation did not complete")
            yield result or GenerationResult(provider="openai", model=self._model)
        except APITimeoutError as exc:
            self._log_failure(exc)
            raise ProviderTimeoutError from exc
        except AuthenticationError as exc:
            self._log_failure(exc)
            raise ProviderAuthenticationError from exc
        except RateLimitError as exc:
            self._log_failure(exc)
            raise ProviderRateLimitError from exc
        except (BadRequestError, NotFoundError) as exc:
            self._log_failure(exc)
            raise ProviderInvalidRequestError from exc
        except APIConnectionError as exc:
            self._log_failure(exc)
            raise ProviderUnavailableError from exc
        except APIStatusError as exc:
            self._log_failure(exc)
            if exc.status_code >= 500:
                raise ProviderUnavailableError from exc
            raise ProviderError from exc
        finally:
            if stream is not None:
                await stream.close()

    @staticmethod
    def _log_failure(exc: Exception) -> None:
        logger.warning(
            "OpenAI request failed",
            extra={"context": {"provider": "openai", "error_type": type(exc).__name__}},
        )
