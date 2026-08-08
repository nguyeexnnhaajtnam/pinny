from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from pinny.chat.errors import (
    ConversationNotFoundError,
    GenerationInProgressError,
    PersistenceError,
)
from pinny.chat.types import ChatMessage, PreparedChat
from pinny.core.config import Settings
from pinny.db.models import Conversation, Message


class SqlAlchemyChatRepository:
    def __init__(
        self, session_factory: async_sessionmaker[AsyncSession], settings: Settings
    ) -> None:
        self._sessions = session_factory
        self._stale_after = timedelta(seconds=settings.chat_stale_generation_seconds)

    async def prepare(
        self, user_id: str, message: str, conversation_id: UUID | None
    ) -> PreparedChat:
        async with self._sessions() as session:
            try:
                async with session.begin():
                    conversation = await self._load_or_create(session, user_id, conversation_id)
                    stale_before = datetime.now(UTC) - self._stale_after
                    await session.execute(
                        update(Message)
                        .where(
                            Message.conversation_id == conversation.id,
                            Message.role == "assistant",
                            Message.status == "in_progress",
                            Message.created_at < stale_before,
                        )
                        .values(status="interrupted")
                    )
                    active = await session.scalar(
                        select(Message.id).where(
                            Message.conversation_id == conversation.id,
                            Message.role == "assistant",
                            Message.status == "in_progress",
                        )
                    )
                    if active is not None:
                        raise GenerationInProgressError

                    message_time = datetime.now(UTC)
                    user_message = Message(
                        conversation_id=conversation.id,
                        role="user",
                        content=message,
                        status="completed",
                        created_at=message_time,
                    )
                    assistant_message = Message(
                        conversation_id=conversation.id,
                        role="assistant",
                        content="",
                        status="in_progress",
                        created_at=message_time + timedelta(microseconds=1),
                    )
                    session.add_all([user_message, assistant_message])
                    await session.flush()
                    rows = (
                        await session.execute(
                            select(Message.role, Message.content)
                            .where(
                                Message.conversation_id == conversation.id,
                                Message.status == "completed",
                            )
                            .order_by(Message.created_at, Message.id)
                        )
                    ).all()
                    history = [ChatMessage(role=role, content=content) for role, content in rows]
                    prepared = PreparedChat(
                        conversation_id=conversation.id,
                        user_message_id=user_message.id,
                        assistant_message_id=assistant_message.id,
                        history=history,
                    )
                return prepared
            except (ConversationNotFoundError, GenerationInProgressError):
                raise
            except IntegrityError as exc:
                raise GenerationInProgressError from exc
            except SQLAlchemyError as exc:
                raise PersistenceError from exc

    async def _load_or_create(
        self, session: AsyncSession, user_id: str, conversation_id: UUID | None
    ) -> Conversation:
        if conversation_id is None:
            conversation = Conversation(user_id=user_id)
            session.add(conversation)
            await session.flush()
            return conversation
        conversation = await session.scalar(
            select(Conversation)
            .where(Conversation.id == conversation_id, Conversation.user_id == user_id)
            .with_for_update()
        )
        if conversation is None:
            raise ConversationNotFoundError
        return conversation

    async def complete(self, prepared: PreparedChat, content: str) -> None:
        async with self._sessions() as session:
            try:
                async with session.begin():
                    result = await session.execute(
                        update(Message)
                        .where(
                            Message.id == prepared.assistant_message_id,
                            Message.status == "in_progress",
                        )
                        .values(content=content, status="completed")
                    )
                    if result.rowcount != 1:
                        raise PersistenceError("assistant message is no longer active")
                    await session.execute(
                        update(Conversation)
                        .where(Conversation.id == prepared.conversation_id)
                        .values(updated_at=datetime.now(UTC))
                    )
            except PersistenceError:
                raise
            except SQLAlchemyError as exc:
                raise PersistenceError from exc

    async def fail(self, assistant_message_id: UUID, status: str) -> None:
        if status not in {"failed", "interrupted"}:
            raise ValueError("invalid terminal assistant status")
        async with self._sessions() as session:
            try:
                async with session.begin():
                    await session.execute(
                        update(Message)
                        .where(
                            Message.id == assistant_message_id,
                            Message.status == "in_progress",
                        )
                        .values(content="", status=status)
                    )
            except SQLAlchemyError as exc:
                raise PersistenceError from exc
