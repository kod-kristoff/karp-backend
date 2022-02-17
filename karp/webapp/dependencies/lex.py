from typing import Callable, Type
from fastapi import Depends
from sqlalchemy.orm import Session
from starlette.requests import Request

from karp.lex import (
    EntryRepositoryUnitOfWorkFactory,
    EntryUowRepositoryUnitOfWork,
    ResourceUnitOfWork,
)
from karp.webapp.dependencies.database import get_database, get_session
from karp.webapp.dependencies.events import get_eventbus, EventBus
from karp.webapp.dependencies.fastapi_injector import inject_from_req

from karp.db_infrastructure import Database

from karp.lex_infrastructure import (
    SqlEntryUowRepositoryUnitOfWork,
    SqlResourceUnitOfWork,
)
from karp.lex_infrastructure.repositories import SqlResourceRepository


def get_resource_repository(db_session: Session = Depends(get_session)) -> SqlResourceRepository:
    return SqlResourceRepository(db_session)


def get_resource_unit_of_work(
    db_session: Session = Depends(get_session),
    event_bus: EventBus = Depends(get_eventbus),
) -> ResourceUnitOfWork:
    return SqlResourceUnitOfWork(
        event_bus=event_bus,
        session=db_session,
    )

def get_entry_repo_uow(
    db_session: Session = Depends(get_session),
    entry_uow_factory: EntryRepositoryUnitOfWorkFactory = Depends(inject_from_req(EntryRepositoryUnitOfWorkFactory)),
    event_bus: EventBus = Depends(get_eventbus),
) -> EntryUowRepositoryUnitOfWork:
    return SqlEntryUowRepositoryUnitOfWork(
        event_bus=event_bus,
        entry_uow_factory=entry_uow_factory,
        session=db_session,
    )


def get_lex_uc(Use_case_type: Type) -> Callable:
    def factory(
        resource_uow: ResourceUnitOfWork = Depends(get_resource_unit_of_work),
        entry_repo_uow: EntryUowRepositoryUnitOfWork = Depends(get_entry_repo_uow),
    ) -> Use_case_type:
        return Use_case_type(
            resource_uow=resource_uow,
            entry_repo_uow=entry_repo_uow,
        )
    return factory


