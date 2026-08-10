from datetime import datetime
from zoneinfo import ZoneInfo

from pinny.chat.context import ConversationContextBuilder
from pinny.chat.prompt import PINNY_SYSTEM_PROMPT, PromptBuilder
from pinny.chat.runtime_context import RuntimeContext
from pinny.chat.types import ChatMessage


def runtime_context() -> RuntimeContext:
    current = datetime(2026, 8, 10, 12, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
    return RuntimeContext(current, current.date(), "Asia/Ho_Chi_Minh", "vi-VN")


def test_context_builder_limits_recent_history_and_appends_current_once() -> None:
    history = [ChatMessage("user", str(index)) for index in range(5)]
    current = ChatMessage("user", "current")

    result = ConversationContextBuilder(3).build(history, current)

    assert [item.content for item in result] == ["2", "3", "4", "current"]
    assert result.count(current) == 1


def test_prompt_builder_has_explicit_sections_for_first_and_follow_up_turns() -> None:
    builder = PromptBuilder()
    current = ChatMessage("user", "current")
    history = [ChatMessage("user", "old"), ChatMessage("assistant", "answer")]

    first = builder.build(runtime_context(), [], current)
    follow_up = builder.build(runtime_context(), history, current)

    assert first[0].content == PINNY_SYSTEM_PROMPT
    assert "timezone=Asia/Ho_Chi_Minh" in first[1].content
    assert first[2:] == [current]
    assert follow_up[2:] == [*history, current]
    assert all("Pinus data" not in item.content for item in follow_up[2:])
