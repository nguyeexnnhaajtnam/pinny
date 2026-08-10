import json
from uuid import uuid4

from fastapi.testclient import TestClient

from pinny.api.chat import event_stream, get_chat_service_factory, get_current_user_id
from pinny.chat.types import ChatEvent, ChatMessage, PreparedChat
from pinny.main import app


class FakeService:
    def __init__(self) -> None:
        self.prepared = PreparedChat(uuid4(), uuid4(), uuid4(), [], ChatMessage("user", "hello"))
        self.prepare_args = None
        self.interrupted = False

    async def prepare(self, user_id, message, conversation_id):
        self.prepare_args = (user_id, message, conversation_id)
        return self.prepared

    async def stream(self, prepared, _user_id):
        yield ChatEvent(
            "conversation",
            {
                "conversation_id": str(prepared.conversation_id),
                "message_id": str(prepared.user_message_id),
            },
        )
        yield ChatEvent(
            "delta",
            {
                "conversation_id": str(prepared.conversation_id),
                "message_id": str(prepared.assistant_message_id),
                "content": "hi",
            },
        )
        yield ChatEvent(
            "completed",
            {
                "conversation_id": str(prepared.conversation_id),
                "message_id": str(prepared.assistant_message_id),
            },
        )

    async def interrupt(self, _prepared):
        self.interrupted = True


def test_chat_api_streams_pinny_sse_contract() -> None:
    service = FakeService()
    app.dependency_overrides[get_chat_service_factory] = lambda: lambda: service
    app.dependency_overrides[get_current_user_id] = lambda: "resolved-user"
    try:
        with TestClient(app) as client:
            response = client.post("/api/v1/chat", json={"message": "hello"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "event: conversation" in response.text
    assert "event: delta" in response.text
    assert "event: completed" in response.text
    assert json.dumps("hi")[1:-1] in response.text
    assert service.prepare_args == ("resolved-user", "hello", None)


def test_chat_api_rejects_public_user_id() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/chat", json={"message": "hello", "user_id": "evil"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_chat_api_emits_terminal_error_without_completion() -> None:
    service = FakeService()

    async def failed_stream(prepared, _user_id):
        yield ChatEvent(
            "delta",
            {
                "conversation_id": str(prepared.conversation_id),
                "message_id": str(prepared.assistant_message_id),
                "content": "part",
            },
        )
        yield ChatEvent(
            "error",
            {
                "conversation_id": str(prepared.conversation_id),
                "message_id": str(prepared.assistant_message_id),
                "code": "provider_error",
                "message": "Assistant generation failed",
            },
        )

    service.stream = failed_stream
    app.dependency_overrides[get_chat_service_factory] = lambda: lambda: service
    app.dependency_overrides[get_current_user_id] = lambda: "resolved-user"
    try:
        with TestClient(app) as client:
            response = client.post("/api/v1/chat", json={"message": "hello"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "event: error" in response.text
    assert "event: completed" not in response.text


async def test_transport_disconnect_interrupts_and_emits_no_event() -> None:
    service = FakeService()

    class DisconnectedRequest:
        async def is_disconnected(self):
            return True

    events = [
        event
        async for event in event_stream(
            DisconnectedRequest(), service, service.prepared, "resolved-user"
        )
    ]

    assert events == []
    assert service.interrupted
