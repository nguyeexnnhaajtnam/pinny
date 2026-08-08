import asyncio
import logging

from pinny.core.config import get_settings
from pinny.core.logging import configure_logging
from pinny.db.health import check_database


async def validate() -> int:
    settings = get_settings()
    configure_logging(settings.log_level)
    logger = logging.getLogger(__name__)
    try:
        await check_database(settings)
    except Exception as exc:
        logger.error(
            "PostgreSQL connectivity validation failed",
            extra={"context": {"dependency": "postgresql", "error_type": type(exc).__name__}},
        )
        return 1
    logger.info("PostgreSQL connectivity validation succeeded")
    return 0


def main() -> None:
    raise SystemExit(asyncio.run(validate()))


if __name__ == "__main__":
    main()
