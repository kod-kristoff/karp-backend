from karp.domain import auth_service
from karp.services import messagebus, unit_of_work
from karp.infrastructure.sql import sql_unit_of_work
from karp.infrastructure.jwt import jwt_auth_service


def bootstrap(
    resource_uow: unit_of_work.ResourceUnitOfWork = None,
    entry_uows: unit_of_work.EntriesUnitOfWork = None,
    authservice: auth_service.AuthService = None,
) -> messagebus.MessageBus:
    if authservice is None:
        authservice = jwt_auth_service.JWTAuthenticator()
    if resource_uow is None:
        resource_uow = sql_unit_of_work.SqlResourceUnitOfWork()
    if entry_uows is None:
        entry_uows = unit_of_work.EntriesUnitOfWork()
    return messagebus.MessageBus(
        resource_uow=resource_uow, entry_uows=entry_uows, auth_service=authservice
    )
