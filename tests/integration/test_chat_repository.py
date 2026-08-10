import asyncio
import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import delete, select, update

from pinny.chat.errors import ConversationNotFoundError, GenerationInProgressError, PersistenceError
from pinny.chat.repository import SqlAlchemyChatRepository
from pinny.chat.types import GenerationMetadata
from pinny.core.config import Settings, get_settings
from pinny.db.models import Conversation, Message
from pinny.db.session import session_factory

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("PINNY_RUN_INTEGRATION") != "1",
        reason="set PINNY_RUN_INTEGRATION=1 with migrated PostgreSQL available",
    ),
]


@pytest.fixture(autouse=True)
async def clean_chat_tables():
    async with session_factory() as session:
        await session.execute(delete(Message))
        await session.execute(delete(Conversation))
        await session.commit()
    yield


async def test_repository_persists_history_and_filters_failed_messages() -> None:
    repository = SqlAlchemyChatRepository(session_factory, get_settings())
    first = await repository.prepare("owner", "hello", None)
    await repository.mark_streaming(first.assistant_message_id)
    await repository.complete(first, "hi", GenerationMetadata("openai", "test", 12, 2, 3))
    second = await repository.prepare("owner", "follow up", first.conversation_id)

    assert [(item.role, item.content) for item in second.history] == [
        ("user", "hello"),
        ("assistant", "hi"),
    ]
    assert second.current_user_message.content == "follow up"
    await repository.terminate(second.assistant_message_id, "failed")
    third = await repository.prepare("owner", "again", first.conversation_id)
    assert all(item.content != "" for item in third.history)


async def test_repository_enforces_owner_and_active_generation() -> None:
    repository = SqlAlchemyChatRepository(session_factory, get_settings())
    first = await repository.prepare("owner", "hello", None)
    with pytest.raises(ConversationNotFoundError):
        await repository.prepare("other", "steal", first.conversation_id)
    with pytest.raises(GenerationInProgressError):
        await repository.prepare("owner", "overlap", first.conversation_id)


async def test_lifecycle_completion_is_idempotently_terminal() -> None:
    repository = SqlAlchemyChatRepository(session_factory, get_settings())
    prepared = await repository.prepare("owner", "hello", None)
    await repository.terminate(prepared.assistant_message_id, "cancelled")
    await repository.terminate(prepared.assistant_message_id, "failed")
    async with session_factory() as session:
        status = await session.scalar(
            select(Message.status).where(Message.id == prepared.assistant_message_id)
        )
    assert status == "cancelled"
    assert uuid4() != prepared.conversation_id


async def test_stale_generation_is_recovered_before_follow_up() -> None:
    repository = SqlAlchemyChatRepository(
        session_factory,
        Settings(_env_file=None, chat_stale_generation_seconds=1),
    )
    first = await repository.prepare("owner", "hello", None)
    async with session_factory() as session:
        await session.execute(
            update(Message)
            .where(Message.id == first.assistant_message_id)
            .values(created_at=datetime.now(UTC) - timedelta(minutes=1))
        )
        await session.commit()

    follow_up = await repository.prepare("owner", "again", first.conversation_id)

    assert follow_up.conversation_id == first.conversation_id


async def test_repository_bounds_history_and_persists_generation_metadata() -> None:
    repository = SqlAlchemyChatRepository(
        session_factory,
        Settings(_env_file=None, chat_history_max_messages=2),
    )
    first = await repository.prepare("owner", "one", None)
    await repository.mark_streaming(first.assistant_message_id)
    await repository.complete(
        first, "answer-one", GenerationMetadata("gemini", "model-x", 25, 4, 5)
    )
    second = await repository.prepare("owner", "two", first.conversation_id)
    await repository.mark_streaming(second.assistant_message_id)
    await repository.complete(second, "answer-two", GenerationMetadata("gemini", "model-x", 30))
    third = await repository.prepare("owner", "three", first.conversation_id)

    assert [(item.role, item.content) for item in third.history] == [
        ("user", "two"),
        ("assistant", "answer-two"),
    ]
    async with session_factory() as session:
        row = (
            await session.execute(
                select(
                    Message.status,
                    Message.provider,
                    Message.model,
                    Message.latency_ms,
                    Message.input_tokens,
                    Message.output_tokens,
                ).where(Message.id == first.assistant_message_id)
            )
        ).one()
    assert row == ("completed", "gemini", "model-x", 25, 4, 5)


async def test_invalid_lifecycle_transition_does_not_overwrite_terminal_state() -> None:
    repository = SqlAlchemyChatRepository(session_factory, get_settings())
    prepared = await repository.prepare("owner", "hello", None)
    await repository.terminate(prepared.assistant_message_id, "failed")

    with pytest.raises(PersistenceError, match="no longer pending"):
        await repository.mark_streaming(prepared.assistant_message_id)

    await repository.terminate(prepared.assistant_message_id, "cancelled")
    async with session_factory() as session:
        status = await session.scalar(
            select(Message.status).where(Message.id == prepared.assistant_message_id)
        )
    assert status == "failed"


async def test_concurrent_terminal_updates_commit_exactly_one_state() -> None:
    repository = SqlAlchemyChatRepository(session_factory, get_settings())
    prepared = await repository.prepare("owner", "hello", None)
    await repository.mark_streaming(prepared.assistant_message_id)

    await asyncio.gather(
        repository.terminate(prepared.assistant_message_id, "failed"),
        repository.terminate(prepared.assistant_message_id, "cancelled"),
    )

    async with session_factory() as session:
        status = await session.scalar(
            select(Message.status).where(Message.id == prepared.assistant_message_id)
        )
    assert status in {"failed", "cancelled"}
