from enum import StrEnum
from functools import lru_cache

from pydantic import AliasChoices, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(StrEnum):
    OPENAI = "openai"
    GEMINI = "gemini"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="PINNY_", extra="ignore", case_sensitive=False
    )

    app_name: str = "Pinny"
    environment: str = "development"
    log_level: str = "INFO"
    database_host: str = "localhost"
    database_port: int = Field(default=5432, ge=1, le=65535)
    database_name: str = "pinny"
    database_user: str = "pinny"
    database_password: str = "pinny"
    database_connect_timeout: float = Field(default=3.0, gt=0)
    identity_provider: str = "development"
    dev_user_id: str = "dev-user"
    llm_provider: LLMProvider = Field(
        default=LLMProvider.OPENAI,
        validation_alias=AliasChoices("LLM_PROVIDER", "PINNY_LLM_PROVIDER"),
    )
    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-5-mini"
    openai_timeout: float = Field(default=30.0, gt=0)
    gemini_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("GEMINI_API_KEY", "PINNY_GEMINI_API_KEY"),
    )
    gemini_model: str = Field(
        default="gemini-2.5-flash",
        validation_alias=AliasChoices("GEMINI_MODEL", "PINNY_GEMINI_MODEL"),
    )
    gemini_timeout: float = Field(
        default=30.0,
        gt=0,
        validation_alias=AliasChoices("GEMINI_TIMEOUT", "PINNY_GEMINI_TIMEOUT"),
    )
    chat_max_output_tokens: int = Field(default=2048, ge=1)
    chat_max_context_characters: int = Field(default=100_000, ge=1)
    chat_stale_generation_seconds: int = Field(default=300, ge=1)

    @field_validator("llm_provider", mode="before")
    @classmethod
    def normalize_llm_provider(cls, value: object) -> object:
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("openai_model", "gemini_model")
    @classmethod
    def validate_model_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("model must be non-empty")
        return value

    @model_validator(mode="after")
    def validate_identity_configuration(self) -> "Settings":
        if self.identity_provider != "development":
            raise ValueError("unsupported identity provider")
        if not self.dev_user_id.strip():
            raise ValueError("PINNY_DEV_USER_ID must be non-empty")
        if self.environment.lower() == "production":
            raise ValueError("development identity provider is forbidden in production")
        return self

    def validate_active_llm(self) -> "Settings":
        key = (
            self.openai_api_key if self.llm_provider is LLMProvider.OPENAI else self.gemini_api_key
        )
        if key is None or not key.get_secret_value().strip():
            variable = (
                "PINNY_OPENAI_API_KEY"
                if self.llm_provider is LLMProvider.OPENAI
                else "GEMINI_API_KEY"
            )
            raise ValueError(f"{variable} must be configured for {self.llm_provider.value}")
        return self

    @property
    def sqlalchemy_database_url(self) -> str:
        from urllib.parse import quote_plus

        return (
            "postgresql+asyncpg://"
            f"{quote_plus(self.database_user)}:{quote_plus(self.database_password)}@"
            f"{self.database_host}:{self.database_port}/{quote_plus(self.database_name)}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
