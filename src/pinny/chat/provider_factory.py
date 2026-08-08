from pinny.chat.gemini_provider import GeminiChatModel
from pinny.chat.openai_provider import OpenAIChatModel
from pinny.chat.ports import ChatModel
from pinny.core.config import LLMProvider, Settings


def create_chat_model(settings: Settings) -> ChatModel:
    settings.validate_active_llm()
    if settings.llm_provider is LLMProvider.OPENAI:
        return OpenAIChatModel(settings)
    if settings.llm_provider is LLMProvider.GEMINI:
        return GeminiChatModel(settings)
    raise ValueError("unsupported LLM provider")
