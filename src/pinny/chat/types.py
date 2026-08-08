from dataclasses import dataclass
from typing import Literal
from uuid import UUID


@dataclass(frozen=True)
class ChatMessage:
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass(frozen=True)
class PreparedChat:
    conversation_id: UUID
    user_message_id: UUID
    assistant_message_id: UUID
    history: list[ChatMessage]


@dataclass(frozen=True)
class ChatEvent:
    event: Literal["conversation", "delta", "completed", "error"]
    data: dict[str, str]
