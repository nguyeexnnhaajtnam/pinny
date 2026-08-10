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
from pinny.chat.types import ChatMessage, GenerationMetadata, PreparedChat
from pinny.core.config import Settings
from pinny.db.models import Conversation, Message


class SqlAlchemyChatRepository:
    def __init__(
        self, session_factory: async_sessionmaker[AsyncSession], settings: Settings
    ) -> None:
        self._sessions = session_factory
        self._stale_after = timedelta(seconds=settings.chat_stale_generation_seconds)
        self._history_limit = settings.chat_history_max_messages

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
                            Message.status.in_(("pending", "streaming")),
                            Message.created_at < stale_before,
                        )
                        .values(status="cancelled")
                    )
                    active = await session.scalar(
                        select(Message.id).where(
                            Message.conversation_id == conversation.id,
                            Message.role == "assistant",
                            Message.status.in_(("pending", "streaming")),
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
                        status="pending",
                        created_at=message_time + timedelta(microseconds=1),
                    )
                    session.add_all([user_message, assistant_message])
                    await session.flush()
                    rows = list(
                        await session.execute(
                            select(Message.role, Message.content)
                            .where(
                                Message.conversation_id == conversation.id,
                                Message.status == "completed",
                                Message.id != user_message.id,
                            )
                            .order_by(Message.created_at.desc(), Message.id.desc())
                            .limit(self._history_limit)
                        )
                    )
                    history = [
                        ChatMessage(role=role, content=content) for role, content in reversed(rows)
                    ]
                    prepared = PreparedChat(
                        conversation_id=conversation.id,
                        user_message_id=user_message.id,
                        assistant_message_id=assistant_message.id,
                        history=history,
                        current_user_message=ChatMessage(role="user", content=message),
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

    async def mark_streaming(self, assistant_message_id: UUID) -> None:
        async with self._sessions() as session:
            try:
                async with session.begin():
                    result = await session.execute(
                        update(Message)
                        .where(Message.id == assistant_message_id, Message.status == "pending")
                        .values(status="streaming")
                    )
                    if result.rowcount != 1:
                        raise PersistenceError("assistant message is no longer pending")
            except PersistenceError:
                raise
            except SQLAlchemyError as exc:
                raise PersistenceError from exc

    async def complete(
        self, prepared: PreparedChat, content: str, metadata: GenerationMetadata
    ) -> None:
        async with self._sessions() as session:
            try:
                async with session.begin():
                    result = await session.execute(
                        update(Message)
                        .where(
                            Message.id == prepared.assistant_message_id,
                            Message.status == "streaming",
                        )
                        .values(
                            content=content,
                            status="completed",
                            provider=metadata.provider,
                            model=metadata.model,
                            latency_ms=metadata.latency_ms,
                            input_tokens=metadata.input_tokens,
                            output_tokens=metadata.output_tokens,
                        )
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

    async def terminate(
        self,
        assistant_message_id: UUID,
        status: str,
        metadata: GenerationMetadata | None = None,
    ) -> None:
        if status not in {"failed", "cancelled"}:
            raise ValueError("invalid terminal assistant status")
        async with self._sessions() as session:
            try:
                async with session.begin():
                    await session.execute(
                        update(Message)
                        .where(
                            Message.id == assistant_message_id,
                            Message.status.in_(("pending", "streaming")),
                        )
                        .values(
                            content="",
                            status=status,
                            provider=metadata.provider if metadata else None,
                            model=metadata.model if metadata else None,
                            latency_ms=metadata.latency_ms if metadata else None,
                            input_tokens=metadata.input_tokens if metadata else None,
                            output_tokens=metadata.output_tokens if metadata else None,
                        )
                    )
            except SQLAlchemyError as exc:
                raise PersistenceError from exc
