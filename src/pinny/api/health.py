import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from pinny.core.config import Settings, get_settings
from pinny.db.health import check_database

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/live")
async def liveness() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/ready")
async def readiness(
    response: Response, settings: Annotated[Settings, Depends(get_settings)]
) -> dict[str, object]:
    try:
        await check_database(settings)
    except Exception as exc:
        logger.warning(
            "Readiness dependency check failed",
            extra={"context": {"dependency": "postgresql", "error_type": type(exc).__name__}},
        )
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not_ready", "dependencies": {"postgresql": "unavailable"}}
    return {"status": "ready", "dependencies": {"postgresql": "available"}}
