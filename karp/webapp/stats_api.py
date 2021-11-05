from fastapi import (APIRouter, Depends, HTTPException, Response, Security,
                     status)

from karp import auth
from karp.foundation.value_objects import PermissionLevel
from karp.search.application.queries import EntryQuery
from karp.webapp import schemas

from .app_config import get_current_user
from .fastapi_injector import inject_from_req


router = APIRouter(tags=["Statistics"])


@router.get("/stats/{resource_id}/{field}")
def get_field_values(
    resource_id: str,
    field: str,
    user: auth.User = Security(get_current_user, scopes=["read"]),
    auth_service: auth.AuthService = Depends(inject_from_req(auth.AuthService)),
    entry_query: EntryQuery = Depends(inject_from_req(EntryQuery)),
):
    if not auth_service.authorize(PermissionLevel.read, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="read"'},
        )
    print("calling statistics ...")
    return entry_query.statistics(resource_id, field, bus.ctx)


def init_app(app):
    app.include_router(router)
