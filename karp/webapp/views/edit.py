from os import stat
from fastapi import APIRouter, Security, HTTPException, status

from karp import schemas
from karp.application import ctx
from karp.auth.user import User
from karp.webapp.auth import get_current_user

from flask import Blueprint  # pyre-ignore
from flask import jsonify as flask_jsonify  # pyre-ignore
from flask import request  # pyre-ignore

from karp.resourcemgr import entrywrite
from karp.errors import KarpError
import karp.auth.auth as auth
from karp.util import convert

edit_api = Blueprint("edit_api", __name__)

router = APIRouter()


@router.post("/{resource_id}/add")
def add_entry(
    resource_id: str,
    data: schemas.EntryAdd,
    user: User = Security(get_current_user, scopes=["write"]),
):
    if not ctx.auth_service.authorize(
        schemas.PermissionLevel.write, user, [resource_id]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="write"'},
        )
    print("calling entrywrite")
    new_id = entrywrite.add_entry(
        resource_id, data.entry, user.identifier, message=data.message
    )
    return flask_jsonify({"newID": new_id}), 201


# @edit_api.route("/<resource_id>/<entry_id>/update", methods=["POST"])
# @auth.auth.authorization("WRITE", add_user=True)
# def update_entry(user, resource_id, entry_id):
#     force_update = convert.str2bool(request.args.get("force", "false"))
#     data = request.get_json()
#     version = data.get("version")
#     entry = data.get("entry")
#     message = data.get("message")
#     if not (version and entry and message):
#         raise KarpError("Missing version, entry or message")
#     try:
#         new_id = entrywrite.update_entry(
#             resource_id,
#             entry_id,
#             version,
#             entry,
#             user.identifier,
#             message=message,
#             force=force_update,
#         )
#         return flask_jsonify({"newID": new_id}), 200
#     except entrywrite.UpdateConflict as err:
#         return flask_jsonify(err.error_obj), 400


# @edit_api.route("/<resource_id>/<entry_id>/delete", methods=["DELETE"])
# @auth.auth.authorization("WRITE", add_user=True)
# def delete_entry(user, resource_id: str, entry_id: str):
#     """Delete a entry from a resource.

#     Arguments:
#         user {karp.auth.user.User} -- [description]
#         resource_id {str} -- [description]
#         entry_id {str} -- [description]

#     Returns:
#         [type] -- [description]
#     """
#     entrywrite.delete_entry(resource_id, entry_id, user.identifier)
#     return "", 204


# @edit_api.route("/<resource_id>/preview", methods=["POST"])
# @auth.auth.authorization("READ")
# def preview_entry(resource_id):
#     data = request.get_json()
#     preview = entrywrite.preview_entry(resource_id, data)
#     return flask_jsonify(preview)


def init_app(app):
    app.include_router(router)
