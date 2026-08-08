from unittest.mock import AsyncMock

from fastapi.testclient import TestClient


def test_liveness_reports_alive(client: TestClient) -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_readiness_reports_available_database(client: TestClient, monkeypatch) -> None:
    check = AsyncMock(return_value=None)
    monkeypatch.setattr("pinny.api.health.check_database", check)

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["dependencies"]["postgresql"] == "available"


def test_readiness_reports_unavailable_database(client: TestClient, monkeypatch) -> None:
    check = AsyncMock(side_effect=OSError("connection refused"))
    monkeypatch.setattr("pinny.api.health.check_database", check)

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "dependencies": {"postgresql": "unavailable"},
    }
