from fastapi import HTTPException, status
from karp import auth


def authorize_user(
    auth_service: auth.AuthService,
    user: auth.User,
    level: auth.PermissionLevel,
    resource_ids: list[str],
):
    if not auth_service.authorize(level, user, resource_ids):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": f'Bearer scope="lexica:{str(level).lower()}'},
        )
