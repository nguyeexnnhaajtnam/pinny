from collections.abc import AsyncIterator
from typing import Protocol
from uuid import UUID

from pinny.chat.types import ChatMessage, PreparedChat


class CurrentUserProvider(Protocol):
    async def get_current_user_id(self) -> str: ...


class ChatModel(Protocol):
    def stream(self, messages: list[ChatMessage], user_id: str) -> AsyncIterator[str]: ...


class ChatRepository(Protocol):
    async def prepare(
        self, user_id: str, message: str, conversation_id: UUID | None
    ) -> PreparedChat: ...

    async def complete(self, prepared: PreparedChat, content: str) -> None: ...

    async def fail(self, assistant_message_id: UUID, status: str) -> None: ...
