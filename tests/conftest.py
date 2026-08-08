from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from pinny.core.config import get_settings
from pinny.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    get_settings.cache_clear()
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()
