import asyncio
from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest

from pinny.chat.context import ConversationContextBuilder
from pinny.chat.errors import (
    ContextLimitError,
    ProviderInvalidRequestError,
    ProviderUnavailableError,
)
from pinny.chat.prompt import PromptBuilder
from pinny.chat.runtime_context import RuntimeContext
from pinny.chat.service import ChatService
from pinny.chat.types import (
    ChatMessage,
    GenerationMetadata,
    GenerationResult,
    PreparedChat,
    TextDelta,
)


class FakeRepository:
    def __init__(self, prepared: PreparedChat, prepare_error: Exception | None = None) -> None:
        self.prepared = prepared
        self.prepare_error = prepare_error
        self.completed: tuple[str, GenerationMetadata] | None = None
        self.streaming = False
        self.terminals: list[str] = []

    async def prepare(self, _user_id, _message, _conversation_id):
        if self.prepare_error:
            raise self.prepare_error
        return self.prepared

    async def mark_streaming(self, _assistant_message_id):
        self.streaming = True

    async def complete(self, _prepared, content: str, metadata: GenerationMetadata) -> None:
        self.completed = (content, metadata)

    async def terminate(self, _assistant_message_id, status: str, metadata=None) -> None:
        self.terminals.append(status)


class FakeRuntimeProvider:
    async def get_runtime_context(self) -> RuntimeContext:
        current = datetime(2026, 8, 10, 12, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
        return RuntimeContext(current, current.date(), "Asia/Ho_Chi_Minh", "vi-VN")


class FakeModel:
    def __init__(self, attempts: list[list[object]]) -> None:
        self.attempts = attempts
        self.calls = 0
        self.messages = None

    async def stream(self, messages, _user_id):
        self.messages = messages
        items = self.attempts[self.calls]
        self.calls += 1
        for item in items:
            if isinstance(item, Exception):
                raise item
            yield item


def prepared(history=None) -> PreparedChat:
    return PreparedChat(
        uuid4(),
        uuid4(),
        uuid4(),
        history or [],
        ChatMessage("user", "current"),
    )


def service(repo: FakeRepository, model, *, max_chars=1000, attempts=2, timeout=1) -> ChatService:
    return ChatService(
        repo,
        model,
        max_chars,
        FakeRuntimeProvider(),
        ConversationContextBuilder(20),
        PromptBuilder(),
        timeout,
        attempts,
        0,
    )


async def test_success_streams_and_persists_metadata_before_completed_event() -> None:
    repo = FakeRepository(prepared([ChatMessage("user", "old")]))
    model = FakeModel(
        [[TextDelta("xin"), TextDelta(" chao"), GenerationResult("openai", "test", 4, 2)]]
    )
    chat = service(repo, model)

    session = await chat.prepare("user", "current", None)
    events = [event async for event in chat.stream(session, "user")]

    assert [event.event for event in events] == ["conversation", "delta", "delta", "completed"]
    assert repo.completed is not None
    assert repo.completed[0] == "xin chao"
    assert repo.completed[1].provider == "openai"
    assert events[1].data["message_id"] == str(session.assistant_message_id)
    assert model.messages[0].role == "system"
    assert model.messages[-1] == ChatMessage("user", "current")


async def test_retryable_pre_delta_failure_retries_but_post_delta_failure_does_not() -> None:
    repo = FakeRepository(prepared())
    model = FakeModel(
        [
            [ProviderUnavailableError()],
            [TextDelta("ok"), GenerationResult("gemini", "test")],
        ]
    )
    chat = service(repo, model)
    session = await chat.prepare("user", "current", None)

    events = [event async for event in chat.stream(session, "user")]

    assert model.calls == 2
    assert events[-1].event == "completed"

    repo2 = FakeRepository(prepared())
    model2 = FakeModel([[TextDelta("partial"), ProviderUnavailableError()]])
    session2 = await service(repo2, model2).prepare("user", "current", None)
    events2 = [event async for event in service(repo2, model2).stream(session2, "user")]
    assert model2.calls == 1
    assert [item.event for item in events2][-1] == "error"


async def test_non_retryable_failure_marks_failed_and_emits_safe_error() -> None:
    repo = FakeRepository(prepared())
    model = FakeModel([[ProviderInvalidRequestError("sensitive")]])
    chat = service(repo, model)
    session = await chat.prepare("user", "current", None)

    events = [event async for event in chat.stream(session, "user")]

    assert model.calls == 1
    assert repo.terminals == ["failed"]
    assert events[-1].data["code"] == "provider_invalid_request"
    assert "sensitive" not in str(events[-1].data)


async def test_timeout_is_bounded_and_exhausts_configured_attempts() -> None:
    repo = FakeRepository(prepared())

    class SlowModel:
        def __init__(self) -> None:
            self.calls = 0

        async def stream(self, _messages, _user_id):
            self.calls += 1
            await asyncio.sleep(1)
            yield TextDelta("late")

    model = SlowModel()
    chat = service(repo, model, attempts=2, timeout=0.001)
    session = await chat.prepare("user", "current", None)

    events = [event async for event in chat.stream(session, "user")]

    assert model.calls == 2
    assert events[-1].event == "error"
    assert events[-1].data["code"] == "provider_timeout"
    assert repo.terminals == ["failed"]


async def test_context_limit_fails_pending_generation() -> None:
    repo = FakeRepository(prepared([ChatMessage("user", "too long")]))
    chat = service(repo, FakeModel([]), max_chars=2)

    with pytest.raises(ContextLimitError):
        await chat.prepare("user", "message", None)
    assert repo.terminals == ["failed"]


async def test_cancellation_marks_cancelled() -> None:
    repo = FakeRepository(prepared())

    class CancelModel:
        async def stream(self, _messages, _user_id):
            raise asyncio.CancelledError
            yield TextDelta("unreachable")

    chat = service(repo, CancelModel())
    session = await chat.prepare("user", "current", None)
    with pytest.raises(asyncio.CancelledError):
        _ = [event async for event in chat.stream(session, "user")]
    assert repo.terminals == ["cancelled"]
