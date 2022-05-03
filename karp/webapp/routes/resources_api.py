from typing import Dict, List

from fastapi import APIRouter, Body, Depends
from starlette import status

from karp.auth.application.queries import GetResourcePermissions, ResourcePermissionDto

from karp.lex.domain.entities import create_resource
from karp.lex_infrastructure.repositories.async_sql_resources import AsyncSqlResourceRepository

from karp.webapp.dependencies.database import get_repository
from karp.webapp.schemas import ResourceCreate, ResourcePublic
from karp.webapp.fastapi_injector import inject_from_req


router = APIRouter(tags=["Resources"])
new_router = APIRouter()


@new_router.get('/resources')
async def get_all_resources() -> List[Dict]:
    resources = [
        {'resource_id': 'places'},
    ]
    return resources


@new_router.post(
    '/resources',
    response_model=ResourcePublic,
    status_code=status.HTTP_201_CREATED
)
async def create_new_resource(
    new_resource: ResourceCreate = Body(...),
    resource_repo: AsyncSqlResourceRepository = Depends(get_repository(AsyncSqlResourceRepository)),
) -> ResourcePublic:
    data = new_resource.dict()
    del data['user']
    data['created_by'] = new_resource.user
    resource = create_resource(**data)
    await resource_repo.save(resource)
    return resource.dict()


@router.get(
    "/resources",
    response_model=List[ResourcePermissionDto])
def list_resource_permissions(
    query: GetResourcePermissions = Depends(inject_from_req(GetResourcePermissions)),
):
    return query.query()


def init_app(app):
    app.include_router(router)
