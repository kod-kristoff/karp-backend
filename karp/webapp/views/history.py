from typing import Optional

from fastapi import APIRouter, Query, Security, HTTPException, status

from karp.domain.models.user import User
from karp.domain.models.auth_service import PermissionLevel

from karp.application import ctx
from karp.application.services import entries

from karp.webapp.auth import get_current_user

# from flask import Blueprint, jsonify, request  # pyre-ignore

# import karp.auth.auth as auth
# import karp.resourcemgr.entryread as entryread
# import karp.resourcemgr as resourcemgr
# import karp.errors as errors

router = APIRouter()
#
#
# @history_api.route("/<resource_id>/<entry_id>/diff", methods=["GET", "POST"])
# @auth.auth.authorization("ADMIN")
# def get_diff(resource_id, entry_id):
#     from_version = request.args.get("from_version")
#     to_version = request.args.get("to_version")
#     from_date_str = request.args.get("from_date")
#     to_date_str = request.args.get("to_date")
#     from_date = None
#     to_date = None
#     try:
#         if from_date_str:
#             from_date = float(from_date_str)
#         if to_date_str:
#             to_date = float(to_date_str)
#     except ValueError:
#         raise errors.KarpError("Wrong date format", code=50)
#
#     diff_parameters = {
#         "from_date": from_date,
#         "to_date": to_date,
#         "from_version": from_version,
#         "to_version": to_version,
#         "entry": request.get_json(),
#     }
#
#     diff, from_version, to_version = entryread.diff(
#         resourcemgr.get_resource(resource_id), entry_id, **diff_parameters
#     )
#     result = {"diff": diff, "from_version": from_version}
#     if to_version:
#         result["to_version"] = to_version
#     return jsonify(result)


@router.get(
    "/{resource_id}/history",
)
def get_history(
    resource_id: str,
    user: User = Security(get_current_user, scopes=["admin"]),
    user_id: Optional[str] = Query(None),
    entry_id: Optional[str] = Query(None),
    from_date: Optional[float] = Query(None),
    to_date: Optional[float] = Query(None),
    to_version: Optional[int] = Query(None),
    from_version: Optional[int] = Query(None),
    current_page: int = Query(0),
    page_size: int = Query(100),
):
    if not ctx.auth_service.authorize(PermissionLevel.admin, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="admin"'},
        )
    history, total = entries.get_history(
        resource_id,
        page_size=page_size,
        current_page=current_page,
        from_date=from_date,
        to_date=to_date,
        user_id=user_id,
        entry_id=entry_id,
        from_version=from_version,
        to_version=to_version,
    )
    return {"history": history, "total": total}


@router.get("/{resource_id}/{entry_id}/{version}/history")
# @auth.auth.authorization("ADMIN")
def get_history_for_entry(
    resource_id: str,
    entry_id: str,
    version: int,
    user: User = Security(get_current_user, scopes=["admin"]),
):
    historical_entry = entries.get_entry_history(resource_id, entry_id, version)
    return historical_entry


def init_app(app):
    app.include_router(router)
