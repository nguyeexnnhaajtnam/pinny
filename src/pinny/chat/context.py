from pinny.chat.types import ChatMessage


class ConversationContextBuilder:
    def __init__(self, max_messages: int) -> None:
        if max_messages < 1:
            raise ValueError("max_messages must be positive")
        self._max_messages = max_messages

    def build(
        self, completed_history: list[ChatMessage], current_user_message: ChatMessage
    ) -> list[ChatMessage]:
        eligible = [item for item in completed_history if item.role in {"user", "assistant"}]
        return [*eligible[-self._max_messages :], current_user_message]
