import logging
import typing

import pydantic
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Security,
    status,
)

from karp import auth
from karp.api import dependencies as deps
from karp.api.dependencies.fastapi_injector import inject_from_req
from karp.auth.application import ResourcePermissionQueries
from karp.foundation.value_objects import PermissionLevel
from karp.lex.domain.errors import ResourceNotFound
from karp.search.infrastructure.es import EsSearchService

logger = logging.getLogger(__name__)


router = APIRouter()


class StatisticsDto(pydantic.BaseModel):
    value: str
    count: int


@router.get(
    "/{resource_id}/{field}",
    response_model=typing.List[StatisticsDto],
)
def get_field_values(
    resource_id: str,
    field: str,
    user: auth.User = Security(deps.get_user_optional, scopes=["read"]),
    resource_permissions: ResourcePermissionQueries = Depends(deps.get_resource_permissions),
    search_service: EsSearchService = Depends(inject_from_req(EsSearchService)),
    published_resources: [str] = Depends(deps.get_published_resources),
):
    if not resource_permissions.has_permission(PermissionLevel.read, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    if resource_id not in published_resources:
        raise ResourceNotFound(resource_id)
    logger.debug(f"calling statistics ... from {search_service=}")
    return search_service.statistics(resource_id, field)
