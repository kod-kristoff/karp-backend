# from typing import Tuple

# from karp.database import db
# from karp import application
from karp.application.context import Context
from karp.domain.errors import RepositoryStatusError
from karp.infrastructure.unit_of_work import unit_of_work


class SystemMonitorResponse:
    def __init__(self):
        self.message = None

    def __bool__(self):
        return True


class SystemOk(SystemMonitorResponse):
    def __bool__(self):
        return True


class SystemNotOk(SystemMonitorResponse):
    def __init__(self, message: str):
        self.message = message

    def __bool__(self):
        return False


def check_database_status(context: Context) -> SystemMonitorResponse:
    print(f"context = {context!r}")
    if context.resource_repo is None:
        return SystemNotOk(message="No resource_repository is configured.")
    try:
        # to check database we will execute raw query
        with unit_of_work(using=context.resource_repo) as uw:
            uw.check_status()
    except RepositoryStatusError as e:
        return SystemNotOk(message=str(e))

    return SystemOk()
