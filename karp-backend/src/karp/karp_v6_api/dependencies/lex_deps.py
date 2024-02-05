from fastapi import Depends
from karp.karp_v6_api.dependencies import db_deps
from karp.karp_v6_api.dependencies.db_deps import (
    get_session,
)
from karp.lex_infrastructure import (
    GenericGetEntryDiff,
    GenericGetEntryHistory,
    GenericGetHistory,
    SqlGetPublishedResources,
    SqlReadOnlyResourceRepository,
    SqlResourceUnitOfWork,
)
from sqlalchemy.orm import Session
from starlette.requests import Request  # noqa: F401


def get_resource_unit_of_work(
    db_session: Session = Depends(get_session),
) -> SqlResourceUnitOfWork:
    return SqlResourceUnitOfWork(
        session=db_session,
    )


def get_resources_read_repo(  # noqa: D103
    session: Session = Depends(get_session),
) -> SqlReadOnlyResourceRepository:
    return SqlReadOnlyResourceRepository(session)


def get_published_resources(  # noqa: D103
    session: Session = Depends(get_session),
) -> SqlGetPublishedResources:
    return SqlGetPublishedResources(session)


def get_entry_diff(  # noqa: D103
    resource_uow: SqlResourceUnitOfWork = Depends(get_resource_unit_of_work),
) -> GenericGetEntryDiff:
    return GenericGetEntryDiff(
        resource_uow=resource_uow,
    )


def get_entry_history(  # noqa: D103
    resource_uow: SqlResourceUnitOfWork = Depends(get_resource_unit_of_work),
) -> GenericGetEntryHistory:
    return GenericGetEntryHistory(
        resource_uow=resource_uow,
    )


def get_history(  # noqa: D103
    resource_uow: SqlResourceUnitOfWork = Depends(get_resource_unit_of_work),
) -> GenericGetHistory:
    return GenericGetHistory(
        resource_uow=resource_uow,
    )
