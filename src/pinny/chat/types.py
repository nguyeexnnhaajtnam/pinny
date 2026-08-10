from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from pinny.chat.runtime_context import RuntimeContext


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
    current_user_message: ChatMessage
    runtime_context: RuntimeContext | None = None


@dataclass(frozen=True)
class TextDelta:
    text: str


@dataclass(frozen=True)
class GenerationResult:
    provider: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None


StreamItem = TextDelta | GenerationResult


@dataclass(frozen=True)
class GenerationMetadata:
    provider: str | None
    model: str | None
    latency_ms: int
    input_tokens: int | None = None
    output_tokens: int | None = None


@dataclass(frozen=True)
class ChatEvent:
    event: Literal["conversation", "delta", "completed", "error"]
    data: dict[str, str]
