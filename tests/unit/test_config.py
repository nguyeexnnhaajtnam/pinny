import pytest
from pydantic import ValidationError

from pinny.core.config import Settings


def test_settings_have_safe_local_defaults(monkeypatch) -> None:
    monkeypatch.delenv("PINNY_DATABASE_HOST", raising=False)
    settings = Settings(_env_file=None)

    assert settings.environment == "development"
    assert settings.database_host == "localhost"
    assert settings.database_connect_timeout > 0


def test_settings_load_prefixed_environment(monkeypatch) -> None:
    monkeypatch.setenv("PINNY_DATABASE_HOST", "database.internal")

    assert Settings(_env_file=None).database_host == "database.internal"


def test_openai_secret_is_masked() -> None:
    settings = Settings(_env_file=None, openai_api_key="private-key")

    assert "private-key" not in repr(settings)


def test_development_identity_must_be_non_empty() -> None:
    with pytest.raises(ValidationError, match="PINNY_DEV_USER_ID"):
        Settings(_env_file=None, dev_user_id=" ")


def test_development_identity_is_forbidden_in_production() -> None:
    with pytest.raises(ValidationError, match="forbidden in production"):
        Settings(_env_file=None, environment="production")
