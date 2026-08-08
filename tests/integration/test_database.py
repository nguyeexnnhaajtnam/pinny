import os

import pytest

from pinny.core.config import Settings
from pinny.db.health import check_database


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("PINNY_RUN_INTEGRATION") != "1",
    reason="set PINNY_RUN_INTEGRATION=1 with PostgreSQL available",
)
async def test_configured_postgresql_is_reachable() -> None:
    await check_database(Settings())
