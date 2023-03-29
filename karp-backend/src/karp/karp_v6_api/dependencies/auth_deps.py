import logging  # noqa: D100, I001
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.param_functions import Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, SecurityScopes
from fastapi.security import utils as security_utils
import logging  # noqa: F811

# from karp import bootstrap, services
from karp import auth, lex

# from karp.auth.auth import auth
from karp.main.errors import ClientErrorCodes, KarpError  # noqa: F401
from karp.auth.domain.auth_service import AuthService  # noqa: F401
from karp.auth_infrastructure import (
    JWTAuthService,
    LexGetResourcePermissions,
    LexIsResourceProtected,
)
from . import lex_deps
from .fastapi_injector import inject_from_req


# auto_error false is needed so that FastAPI does not
# give back a faulty 403 when credentials are missing
auth_scheme = HTTPBearer(auto_error=False)

logger = logging.getLogger(__name__)


def bearer_scheme(authorization=Header(None)):  # noqa: ANN201, D103
    if not authorization:
        return None
    scheme, credentials = security_utils.get_authorization_scheme_param(authorization)
    if not (scheme and credentials):
        return None
    return HTTPAuthorizationCredentials(scheme=scheme, credentials=credentials)


def get_resource_permissions(  # noqa: D103
    query: lex.GetPublishedResources = Depends(lex_deps.get_published_resources),
) -> auth.GetResourcePermissions:
    return LexGetResourcePermissions(query)


# def get_resource_permissions(conn: Connection = Depends(database.get_connection)) -> GetResourcePermissions:
#     return


def get_is_resource_protected(  # noqa: D103
    repo: lex.ReadOnlyResourceRepository = Depends(lex_deps.get_resources_read_repo),
) -> auth.IsResourceProtected:
    return LexIsResourceProtected(repo)


def get_auth_service(  # noqa: D103
    config: auth.AuthServiceConfig = Depends(inject_from_req(auth.AuthServiceConfig)),
    query: auth.IsResourceProtected = Depends(get_is_resource_protected),
) -> auth.AuthService:
    return JWTAuthService(
        pubkey_path=config.pubkey_path,
        is_resource_protected=query,
    )


def get_current_user(  # noqa: D103
    security_scopes: SecurityScopes,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    auth_service: auth.AuthService = Depends(get_auth_service),
) -> Optional[auth.User]:
    if not credentials:
        return None
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
        # code=ClientErrorCodes.NOT_PERMITTED,
    )
    try:
        logger.debug(
            "Calling auth_service",
            extra={"credentials": credentials},
        )
        return auth_service.authenticate(credentials.scheme, credentials.credentials)
    except KarpError:
        logger.exception("error authenticating")
        raise credentials_exception


get_user_optional = get_current_user


def get_user(  # noqa: D103
    security_scopes: SecurityScopes,
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
    auth_service: auth.AuthService = Depends(get_auth_service),
) -> auth.User:
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
        # code=ClientErrorCodes.NOT_PERMITTED,
    )
    if not credentials:
        raise credentials_exception
    try:
        logger.debug(
            "Calling auth_service",
            extra={"credentials": credentials},
        )
        return auth_service.authenticate(credentials.scheme, credentials.credentials)
    except KarpError:
        raise credentials_exception
