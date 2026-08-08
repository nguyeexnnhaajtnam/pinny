import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from pinny.api.chat import router as chat_router
from pinny.api.errors import register_error_handlers
from pinny.api.health import router as health_router
from pinny.core.config import get_settings
from pinny.core.logging import configure_logging


@asynccontextmanager
async def lifespan(application: FastAPI):
    settings = get_settings()
    settings.validate_active_llm()
    configure_logging(settings.log_level)
    logging.getLogger(__name__).info(
        "Application started", extra={"context": {"environment": settings.environment}}
    )
    yield
    logging.getLogger(__name__).info("Application stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title=settings.app_name, lifespan=lifespan)
    application.include_router(health_router, prefix="/health")
    application.include_router(chat_router, prefix="/api/v1")
    register_error_handlers(application)
    return application


app = create_app()
