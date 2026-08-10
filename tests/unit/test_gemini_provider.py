import asyncio
from types import SimpleNamespace

import pytest

from pinny.chat.errors import ProviderError
from pinny.chat.gemini_provider import GeminiChatModel
from pinny.chat.types import ChatMessage, GenerationResult, TextDelta
from pinny.core.config import Settings


class FakeStream:
    def __init__(self, chunks) -> None:
        self.chunks = chunks
        self.closed = False

    def __aiter__(self):
        self.iterator = iter(self.chunks)
        return self

    async def __anext__(self):
        try:
            return next(self.iterator)
        except StopIteration as exc:
            raise StopAsyncIteration from exc

    async def aclose(self) -> None:
        self.closed = True


class BlockingStream(FakeStream):
    def __init__(self) -> None:
        super().__init__([])

    def __aiter__(self):
        return self

    async def __anext__(self):
        await asyncio.Event().wait()
        raise StopAsyncIteration


class FakeModels:
    def __init__(self, stream) -> None:
        self.stream = stream
        self.kwargs = None

    async def generate_content_stream(self, **kwargs):
        self.kwargs = kwargs
        return self.stream


def configured_model(stream):
    models = FakeModels(stream)
    client = SimpleNamespace(models=models)
    settings = Settings(
        _env_file=None,
        llm_provider="gemini",
        gemini_api_key="test-key",
        gemini_model="test-gemini",
    )
    return GeminiChatModel(settings, client=client), models


def chunk(text="", finish_reason=None):
    candidates = []
    if finish_reason:
        candidates = [SimpleNamespace(finish_reason=SimpleNamespace(name=finish_reason))]
    return SimpleNamespace(text=text, candidates=candidates)


async def test_gemini_maps_history_streams_deltas_and_closes() -> None:
    stream = FakeStream([chunk("hello "), chunk("world", "STOP")])
    model, models = configured_model(stream)
    messages = [
        ChatMessage(role="system", content="Be Pinny"),
        ChatMessage(role="user", content="Hi"),
        ChatMessage(role="assistant", content="Hello"),
    ]

    assert [item async for item in model.stream(messages, "user")] == [
        TextDelta("hello "),
        TextDelta("world"),
        GenerationResult("gemini", "test-gemini"),
    ]
    assert stream.closed
    assert models.kwargs["model"] == "test-gemini"
    assert models.kwargs["config"].system_instruction == "Be Pinny"
    assert [item.role for item in models.kwargs["contents"]] == ["user", "model"]


@pytest.mark.parametrize(
    "chunks",
    [[], [chunk("", "SAFETY")], [chunk()], [chunk("partial", "MAX_TOKENS")]],
)
async def test_gemini_rejects_empty_or_unsuccessful_stream(chunks) -> None:
    stream = FakeStream(chunks)
    model, _ = configured_model(stream)
    with pytest.raises(ProviderError):
        _ = [item async for item in model.stream([], "user")]
    assert stream.closed


async def test_gemini_sanitizes_unexpected_sdk_failure() -> None:
    class FailingModels:
        async def generate_content_stream(self, **kwargs):
            raise RuntimeError("sensitive upstream response")

    model, _ = configured_model(FakeStream([]))
    model._client = SimpleNamespace(models=FailingModels())
    with pytest.raises(ProviderError) as exc_info:
        _ = [item async for item in model.stream([], "user")]
    assert "sensitive" not in str(exc_info.value)


async def test_gemini_timeout_uses_stable_error_code() -> None:
    class TimeoutModels:
        async def generate_content_stream(self, **kwargs):
            raise TimeoutError

    model, _ = configured_model(FakeStream([]))
    model._client = SimpleNamespace(models=TimeoutModels())
    with pytest.raises(ProviderError) as exc_info:
        _ = [item async for item in model.stream([], "user")]
    assert exc_info.value.code == "provider_timeout"


async def test_gemini_cancellation_closes_stream() -> None:
    stream = BlockingStream()
    model, _ = configured_model(stream)

    async def consume() -> None:
        _ = [item async for item in model.stream([], "user")]

    task = asyncio.create_task(consume())
    await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert stream.closed
