from pinny.core.config import Settings


class DevelopmentCurrentUserProvider:
    """Non-production identity provider replaced by trusted Pinus auth later."""

    def __init__(self, settings: Settings) -> None:
        self._user_id = settings.dev_user_id

    async def get_current_user_id(self) -> str:
        return self._user_id
