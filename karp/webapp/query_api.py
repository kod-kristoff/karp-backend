"""
Query API.
"""
import logging
from typing import List, Optional

from dependency_injector import wiring
from fastapi import APIRouter, Security, HTTPException, status, Query, Path, Depends

from karp import errors as karp_errors

from karp.domain import value_objects, index

from karp.domain.models.user import User

# from karp.domain.models.auth_service import PermissionLevel

# from karp.application import ctx
# from karp.application.services import resources as resources_service

from karp.webapp import schemas

# from karp.webapp.auth import get_current_user
from karp.services import entry_query
from karp.services.auth_service import AuthService
from karp.services.messagebus import MessageBus
from .app_config import get_current_user
from karp.main.containers import AppContainer


_logger = logging.getLogger("karp")


router = APIRouter()


@router.get("/entries/{resource_id}/{entry_ids}")
@wiring.inject
def get_entries_by_id(
    resource_id: str,
    entry_ids: str,
    user: User = Security(get_current_user, scopes=["read"]),
    auth_service: AuthService = Depends(wiring.Provide[AppContainer.auth_service]),
    bus: MessageBus = Depends(wiring.Provide[AppContainer.bus]),
):
    print("webapp.views.get_entries_by_id")
    if not auth_service.authorize(
        value_objects.PermissionLevel.read, user, [resource_id]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="read"'},
        )
    return entry_query.search_ids(resource_id, entry_ids, ctx=bus.ctx)


# @router.get("/{resources}/query")
@router.get("/query/{resources}")
@wiring.inject
def query(
    resources: str = Path(..., regex=r"^\w+(,\w+)*$"),
    q: Optional[str] = Query(None),
    from_: int = Query(0, alias="from"),
    size: int = Query(25),
    lexicon_stats: bool = Query(True),
    # include_fields: Optional[List[str]] = Query(None),
    user: User = Security(get_current_user, scopes=["read"]),
    auth_service: AuthService = Depends(wiring.Provide[AppContainer.auth_service]),
    bus: MessageBus = Depends(wiring.Provide[AppContainer.bus]),
):
    print(
        f"Called 'query' called with resources={resources}, from={from_}m size={size}"
    )
    resource_list = resources.split(",")
    if not auth_service.authorize(
        value_objects.PermissionLevel.read, user, resource_list
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="read"'},
        )
    query_request = index.QueryRequest(
        resource_ids=resource_list,
        q=q,
        from_=from_,
        size=size,
        lexicon_stats=lexicon_stats,
    )
    try:
        response = entry_query.query(query_request, ctx=bus.ctx)

    except karp_errors.KarpError as err:
        _logger.exception(
            "Error occured when calling 'query' with resources='%s' and q='%s'. e.msg='%s'",
            resources,
            q,
            err.message,
        )
        raise
    return response


# @router.get("/{resources}/query_split")
@router.get("/query_split/{resources}")
@wiring.inject
def query_split(
    resources: str = Path(...),
    q: Optional[str] = Query(None),
    from_: int = Query(0, alias="from"),
    size: int = Query(25),
    lexicon_stats: bool = Query(True),
    user: User = Security(get_current_user, scopes=["read"]),
    auth_service: AuthService = Depends(wiring.Provide[AppContainer.auth_service]),
    bus: MessageBus = Depends(wiring.Provide[AppContainer.bus]),
):
    print("webapp.views.query.query_split: called with resources={}".format(resources))
    resource_list = resources.split(",")
    if not auth_service.authorize(
        value_objects.PermissionLevel.read, user, resource_list
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="read"'},
        )
    query_request = index.QueryRequest(
        resource_ids=resource_list,
        q=q,
        from_=from_,
        size=size,
        lexicon_stats=lexicon_stats,
    )
    try:
        response = entry_query.query_split(query_request, ctx=bus.ctx)

    except karp_errors.KarpError as err:
        _logger.exception(
            "Error occured when calling 'query_split' with resources='%s' and q='%s'. msg='%s'",
            resources,
            q,
            err.message,
        )
        raise
    return response


def init_app(app):
    app.include_router(router)
