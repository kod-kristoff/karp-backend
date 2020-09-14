from typing import List

from karp.application import config

from karp.domain.models.user import User
from karp.domain.models.authentication_service import (
    AuthenticationService,
    PermissionLevel,
)


class DummyAuthenticationService(AuthenticationService):
    def __init__(self):
        assert config.TESTING or config.DEBUG, "Don't use this in production!"

    def authenticate(self, scheme: str, credentials: str) -> User:
        return User("dummy", {}, {})

    def authorize(
        self, level: PermissionLevel, user: User, resource_ids: List[str]
    ) -> bool:
        return True
