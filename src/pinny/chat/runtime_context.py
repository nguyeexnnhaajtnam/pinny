from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from pinny.core.config import Settings


@dataclass(frozen=True)
class RuntimeContext:
    current_datetime: datetime
    current_date: date
    timezone: str
    locale: str


class StandaloneRuntimeContextProvider:
    def __init__(
        self,
        settings: Settings,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._timezone_name = settings.chat_timezone
        self._timezone = ZoneInfo(settings.chat_timezone)
        self._locale = settings.chat_locale
        self._clock = clock or (lambda: datetime.now(UTC))

    async def get_runtime_context(self) -> RuntimeContext:
        current = self._clock()
        if current.tzinfo is None:
            raise ValueError("runtime context clock must return an aware datetime")
        localized = current.astimezone(self._timezone)
        return RuntimeContext(
            current_datetime=localized,
            current_date=localized.date(),
            timezone=self._timezone_name,
            locale=self._locale,
        )
