import json
from collections.abc import AsyncIterator, Callable
from functools import lru_cache
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, Field
from sse_starlette.sse import EventSourceResponse

from pinny.chat.identity import DevelopmentCurrentUserProvider
from pinny.chat.provider_factory import create_chat_model
from pinny.chat.repository import SqlAlchemyChatRepository
from pinny.chat.service import ChatService
from pinny.chat.types import PreparedChat
from pinny.core.config import Settings, get_settings
from pinny.db.session import session_factory

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    conversation_id: UUID | None = None
    message: str = Field(min_length=1, max_length=20_000)


async def get_current_user_id(
    settings: Annotated[Settings, Depends(get_settings)],
) -> str:
    return await DevelopmentCurrentUserProvider(settings).get_current_user_id()


@lru_cache
def get_chat_service() -> ChatService:
    settings = get_settings()
    repository = SqlAlchemyChatRepository(session_factory, settings)
    model = create_chat_model(settings)
    return ChatService(repository, model, settings.chat_max_context_characters)


def get_chat_service_factory() -> Callable[[], ChatService]:
    return get_chat_service


def encode_event(event: str, data: dict[str, str]) -> dict[str, str]:
    return {"event": event, "data": json.dumps(data, ensure_ascii=False)}


async def event_stream(
    request: Request,
    service: ChatService,
    prepared: PreparedChat,
    user_id: str,
) -> AsyncIterator[dict[str, str]]:
    stream = service.stream(prepared, user_id)
    try:
        async for event in stream:
            if await request.is_disconnected():
                await service.interrupt(prepared)
                await stream.aclose()
                return
            yield encode_event(event.event, event.data)
    finally:
        await stream.aclose()


@router.post("/chat")
async def chat(
    payload: ChatRequest,
    request: Request,
    user_id: Annotated[str, Depends(get_current_user_id)],
    service_factory: Annotated[Callable[[], ChatService], Depends(get_chat_service_factory)],
) -> EventSourceResponse:
    service = service_factory()
    prepared = await service.prepare(user_id, payload.message, payload.conversation_id)
    return EventSourceResponse(
        event_stream(request, service, prepared, user_id),
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        ping=15,
    )
