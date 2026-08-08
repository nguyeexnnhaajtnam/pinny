from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from pinny.chat.errors import (
    ChatError,
    ContextLimitError,
    ConversationNotFoundError,
    GenerationInProgressError,
    PersistenceError,
    ProviderConfigurationError,
)


def error_payload(code: str, message: str) -> dict[str, dict[str, str]]:
    return {"error": {"code": code, "message": message}}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_error(_request: Request, _exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=error_payload("validation_error", "Request validation failed"),
        )

    @app.exception_handler(ChatError)
    async def chat_error(_request: Request, exc: ChatError) -> JSONResponse:
        status_code = 500
        message = "Chat service failed"
        if isinstance(exc, ConversationNotFoundError):
            status_code, message = 404, "Conversation not found"
        elif isinstance(exc, GenerationInProgressError):
            status_code, message = 409, "A generation is already active"
        elif isinstance(exc, ContextLimitError):
            status_code, message = 413, "Conversation context is too large"
        elif isinstance(exc, ProviderConfigurationError):
            status_code, message = 503, "Chat provider is not configured"
        elif isinstance(exc, PersistenceError):
            status_code, message = 503, "Chat persistence is unavailable"
        return JSONResponse(status_code=status_code, content=error_payload(exc.code, message))
