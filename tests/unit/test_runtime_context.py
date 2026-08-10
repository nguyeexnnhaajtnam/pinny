from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from pinny.chat.runtime_context import StandaloneRuntimeContextProvider
from pinny.core.config import Settings


async def test_runtime_context_uses_configured_timezone_locale_and_clock() -> None:
    settings = Settings(_env_file=None, chat_timezone="Asia/Ho_Chi_Minh", chat_locale="vi-VN")
    provider = StandaloneRuntimeContextProvider(
        settings, clock=lambda: datetime(2026, 8, 10, 0, 30, tzinfo=UTC)
    )

    context = await provider.get_runtime_context()

    assert context.current_datetime.isoformat() == "2026-08-10T07:30:00+07:00"
    assert context.current_date.isoformat() == "2026-08-10"
    assert context.timezone == "Asia/Ho_Chi_Minh"
    assert context.locale == "vi-VN"


@pytest.mark.parametrize(
    ("field", "value"), [("chat_timezone", "Mars/Olympus"), ("chat_locale", "invalid locale")]
)
def test_invalid_runtime_context_configuration_fails(field: str, value: str) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **{field: value})
