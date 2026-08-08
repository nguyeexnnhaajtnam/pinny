import asyncio
from uuid import uuid4

import pytest

from pinny.chat.errors import ContextLimitError, ProviderError
from pinny.chat.service import ChatService
from pinny.chat.types import ChatMessage, PreparedChat


class FakeRepository:
    def __init__(self, prepared: PreparedChat, prepare_error: Exception | None = None) -> None:
        self.prepared = prepared
        self.prepare_error = prepare_error
        self.completed: str | None = None
        self.failed: list[str] = []

    async def prepare(self, _user_id, _message, _conversation_id):
        if self.prepare_error:
            raise self.prepare_error
        return self.prepared

    async def complete(self, _prepared, content: str) -> None:
        self.completed = content

    async def fail(self, _assistant_message_id, status: str) -> None:
        self.failed.append(status)


class FakeModel:
    def __init__(self, chunks=None, error: Exception | None = None) -> None:
        self.chunks = chunks or []
        self.error = error
        self.messages = None

    async def stream(self, messages, _user_id):
        self.messages = messages
        for chunk in self.chunks:
            yield chunk
        if self.error:
            raise self.error


def prepared(history=None) -> PreparedChat:
    return PreparedChat(uuid4(), uuid4(), uuid4(), history or [])


async def test_success_streams_and_persists_before_completed_event() -> None:
    repo = FakeRepository(prepared([ChatMessage(role="user", content="hello")]))
    model = FakeModel(["xin", " chào"])
    service = ChatService(repo, model, 1000)

    session = await service.prepare("user", "hello", None)
    events = [event async for event in service.stream(session, "user")]

    assert [event.event for event in events] == ["conversation", "delta", "delta", "completed"]
    assert repo.completed == "xin chào"
    assert model.messages[0].role == "system"


async def test_provider_failure_marks_failed_and_emits_terminal_error() -> None:
    repo = FakeRepository(prepared())
    service = ChatService(repo, FakeModel(["partial"], ProviderError()), 1000)

    events = [event async for event in service.stream(repo.prepared, "user")]

    assert [event.event for event in events] == ["conversation", "delta", "error"]
    assert repo.completed is None
    assert repo.failed == ["failed"]


async def test_context_limit_fails_placeholder() -> None:
    repo = FakeRepository(prepared([ChatMessage(role="user", content="too long")]))
    service = ChatService(repo, FakeModel(), 2)

    with pytest.raises(ContextLimitError):
        await service.prepare("user", "message", None)
    assert repo.failed == ["failed"]


async def test_prepare_failure_does_not_call_model() -> None:
    error = RuntimeError("database unavailable")
    repo = FakeRepository(prepared(), prepare_error=error)
    model = FakeModel()
    service = ChatService(repo, model, 1000)

    with pytest.raises(RuntimeError, match="database unavailable"):
        await service.prepare("user", "message", None)
    assert model.messages is None


async def test_cancellation_marks_interrupted() -> None:
    repo = FakeRepository(prepared())

    class CancelModel:
        async def stream(self, _messages, _user_id):
            raise asyncio.CancelledError
            yield "unreachable"

    service = ChatService(repo, CancelModel(), 1000)

    with pytest.raises(asyncio.CancelledError):
        _ = [event async for event in service.stream(repo.prepared, "user")]
    assert repo.failed == ["interrupted"]
