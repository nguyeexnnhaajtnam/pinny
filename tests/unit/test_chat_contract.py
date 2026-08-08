from uuid import uuid4

import pytest
from pydantic import ValidationError

from pinny.api.chat import ChatRequest
from pinny.chat.identity import DevelopmentCurrentUserProvider
from pinny.chat.prompt import PINNY_SYSTEM_PROMPT, with_system_prompt
from pinny.chat.types import ChatMessage
from pinny.core.config import Settings


def test_chat_request_is_strict_and_strips_message() -> None:
    request = ChatRequest(message="  hello  ")

    assert request.message == "hello"
    assert request.conversation_id is None


@pytest.mark.parametrize("payload", [{"message": ""}, {"message": "hello", "user_id": "x"}])
def test_chat_request_rejects_invalid_or_identity_fields(payload) -> None:
    with pytest.raises(ValidationError):
        ChatRequest.model_validate(payload)


async def test_development_identity_returns_configured_user() -> None:
    provider = DevelopmentCurrentUserProvider(Settings(_env_file=None, dev_user_id="user-42"))

    assert await provider.get_current_user_id() == "user-42"


def test_system_prompt_precedes_history_without_reordering() -> None:
    history = [
        ChatMessage(role="user", content="one"),
        ChatMessage(role="assistant", content="two"),
        ChatMessage(role="user", content="three"),
    ]

    result = with_system_prompt(history)

    assert result[0] == ChatMessage(role="system", content=PINNY_SYSTEM_PROMPT)
    assert result[1:] == history
    assert uuid4()  # ensure UUID support used by public contract remains available
