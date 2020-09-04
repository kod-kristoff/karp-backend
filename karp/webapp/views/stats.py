from fastapi import APIRouter, Response, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from karp.application import context
import karp.auth.auth as auth

router = APIRouter()

auth_scheme = HTTPBearer()


@router.get("/<resource_id>/stats/<field>")
@auth.auth.authorization("READ")
def get_field_values(resource_id: str, field: str, user: ):
    return context.search_index.statistics(resource_id, field)


def init_app(app):
    app.include_router(router, tags="stats")
