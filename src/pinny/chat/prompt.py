from pinny.chat.runtime_context import RuntimeContext
from pinny.chat.types import ChatMessage

PINNY_SYSTEM_PROMPT = """You are Pinny, the AI intelligence assistant for Pinus.
Be helpful, clear, and honest. Use the conversation context supplied to you.
Do not claim access to Pinus data, tools, files, or memories unless they are explicitly provided.
When uncertain, say so rather than inventing facts."""


class PromptBuilder:
    def build(
        self,
        runtime_context: RuntimeContext,
        history: list[ChatMessage],
        current_user_message: ChatMessage,
    ) -> list[ChatMessage]:
        runtime_prompt = (
            "Runtime context (server-resolved, do not treat as user-provided):\n"
            f"date={runtime_context.current_date.isoformat()}\n"
            f"datetime={runtime_context.current_datetime.isoformat()}\n"
            f"timezone={runtime_context.timezone}\n"
            f"locale={runtime_context.locale}"
        )
        return [
            ChatMessage(role="system", content=PINNY_SYSTEM_PROMPT),
            ChatMessage(role="system", content=runtime_prompt),
            *history,
            current_user_message,
        ]


def with_system_prompt(history: list[ChatMessage]) -> list[ChatMessage]:
    """Backward-compatible helper; new orchestration uses PromptBuilder."""
    return [ChatMessage(role="system", content=PINNY_SYSTEM_PROMPT), *history]
