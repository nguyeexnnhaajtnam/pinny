import asyncio
from hashlib import sha256
from types import SimpleNamespace

import httpx
import pytest
from openai import APITimeoutError

from pinny.chat.errors import ProviderConfigurationError, ProviderError
from pinny.chat.openai_provider import OpenAIChatModel
from pinny.chat.types import ChatMessage
from pinny.core.config import Settings


class FakeStream:
    def __init__(self, events) -> None:
        self.events = events
        self.closed = False

    def __aiter__(self):
        self.iterator = iter(self.events)
        return self

    async def __anext__(self):
        try:
            return next(self.iterator)
        except StopIteration as exc:
            raise StopAsyncIteration from exc

    async def close(self) -> None:
        self.closed = True


class BlockingStream:
    def __init__(self) -> None:
        self.closed = False

    def __aiter__(self):
        return self

    async def __anext__(self):
        await asyncio.Event().wait()
        raise StopAsyncIteration

    async def close(self) -> None:
        self.closed = True


class FakeResponses:
    def __init__(self, stream) -> None:
        self.stream = stream
        self.kwargs = None

    async def create(self, **kwargs):
        self.kwargs = kwargs
        return self.stream


class FailingResponses:
    async def create(self, **_kwargs):
        raise APITimeoutError(request=httpx.Request("POST", "https://api.openai.com/v1/responses"))


def configured_settings() -> Settings:
    return Settings(_env_file=None, openai_api_key="test-key", openai_model="test-model")


def test_missing_api_key_fails_without_client_call() -> None:
    with pytest.raises(ProviderConfigurationError):
        OpenAIChatModel(Settings(_env_file=None))


async def test_adapter_yields_only_text_deltas_and_closes_stream() -> None:
    stream = FakeStream(
        [
            SimpleNamespace(type="response.created"),
            SimpleNamespace(type="response.output_text.delta", delta="a"),
            SimpleNamespace(type="response.output_text.delta", delta="b"),
            SimpleNamespace(type="response.completed"),
        ]
    )
    responses = FakeResponses(stream)
    client = SimpleNamespace(responses=responses)
    model = OpenAIChatModel(configured_settings(), client=client)

    chunks = [
        chunk async for chunk in model.stream([ChatMessage(role="user", content="hi")], "user-1")
    ]

    assert chunks == ["a", "b"]
    assert stream.closed
    assert responses.kwargs["stream"] is True
    assert responses.kwargs["store"] is False
    assert responses.kwargs["safety_identifier"] == sha256(b"user-1").hexdigest()


async def test_incomplete_response_is_sanitized_and_stream_closes() -> None:
    stream = FakeStream([SimpleNamespace(type="response.incomplete")])
    model = OpenAIChatModel(
        configured_settings(), client=SimpleNamespace(responses=FakeResponses(stream))
    )

    with pytest.raises(ProviderError):
        _ = [
            chunk async for chunk in model.stream([ChatMessage(role="user", content="hi")], "user")
        ]
    assert stream.closed


@pytest.mark.parametrize(
    "events",
    [
        [],
        [SimpleNamespace(type="response.completed")],
        [SimpleNamespace(type="response.output_text.delta", delta="partial")],
        [SimpleNamespace(type="error")],
    ],
)
async def test_missing_text_or_successful_terminal_event_fails(events) -> None:
    stream = FakeStream(events)
    model = OpenAIChatModel(
        configured_settings(), client=SimpleNamespace(responses=FakeResponses(stream))
    )
    with pytest.raises(ProviderError):
        _ = [
            chunk async for chunk in model.stream([ChatMessage(role="user", content="hi")], "user")
        ]
    assert stream.closed


async def test_timeout_is_mapped_to_stable_provider_error() -> None:
    model = OpenAIChatModel(
        configured_settings(), client=SimpleNamespace(responses=FailingResponses())
    )

    with pytest.raises(ProviderError) as exc_info:
        _ = [
            chunk async for chunk in model.stream([ChatMessage(role="user", content="hi")], "user")
        ]
    assert exc_info.value.code == "provider_timeout"


async def test_cancellation_closes_provider_stream() -> None:
    stream = BlockingStream()
    model = OpenAIChatModel(
        configured_settings(), client=SimpleNamespace(responses=FakeResponses(stream))
    )

    async def consume() -> None:
        _ = [
            chunk async for chunk in model.stream([ChatMessage(role="user", content="hi")], "user")
        ]

    task = asyncio.create_task(consume())
    await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert stream.closed
