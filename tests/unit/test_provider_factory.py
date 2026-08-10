from types import SimpleNamespace

import pytest

from pinny.chat.gemini_provider import GeminiChatModel
from pinny.chat.openai_provider import OpenAIChatModel
from pinny.chat.provider_factory import create_chat_model
from pinny.core.config import Settings


def test_factory_selects_openai(monkeypatch) -> None:
    sentinel = SimpleNamespace()
    monkeypatch.setattr("pinny.chat.provider_factory.OpenAIChatModel", lambda settings: sentinel)
    settings = Settings(_env_file=None, llm_provider="OPENAI", openai_api_key="key")
    assert create_chat_model(settings) is sentinel


def test_factory_selects_gemini(monkeypatch) -> None:
    sentinel = SimpleNamespace()
    monkeypatch.setattr("pinny.chat.provider_factory.GeminiChatModel", lambda settings: sentinel)
    settings = Settings(_env_file=None, llm_provider="GeMiNi", gemini_api_key="key")
    assert create_chat_model(settings) is sentinel


def test_factory_requires_active_provider_key(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("PINNY_GEMINI_API_KEY", raising=False)
    settings = Settings(_env_file=None, llm_provider="gemini", gemini_api_key=None)
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        create_chat_model(settings)


def test_factory_returns_concrete_provider_types() -> None:
    assert isinstance(
        create_chat_model(Settings(_env_file=None, llm_provider="openai", openai_api_key="key")),
        OpenAIChatModel,
    )
    assert isinstance(
        create_chat_model(Settings(_env_file=None, llm_provider="gemini", gemini_api_key="key")),
        GeminiChatModel,
    )
