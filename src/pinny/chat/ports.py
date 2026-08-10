from collections.abc import AsyncIterator
from typing import Protocol
from uuid import UUID

from pinny.chat.runtime_context import RuntimeContext
from pinny.chat.types import ChatMessage, GenerationMetadata, PreparedChat, StreamItem


class CurrentUserProvider(Protocol):
    async def get_current_user_id(self) -> str: ...


class RuntimeContextProvider(Protocol):
    async def get_runtime_context(self) -> RuntimeContext: ...


class ChatModel(Protocol):
    def stream(self, messages: list[ChatMessage], user_id: str) -> AsyncIterator[StreamItem]: ...


class ChatRepository(Protocol):
    async def prepare(
        self, user_id: str, message: str, conversation_id: UUID | None
    ) -> PreparedChat: ...

    async def mark_streaming(self, assistant_message_id: UUID) -> None: ...

    async def complete(
        self, prepared: PreparedChat, content: str, metadata: GenerationMetadata
    ) -> None: ...

    async def terminate(
        self,
        assistant_message_id: UUID,
        status: str,
        metadata: GenerationMetadata | None = None,
    ) -> None: ...
