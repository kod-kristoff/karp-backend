import logging

from fastapi import APIRouter, Response, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# from flask import Blueprint  # pyre-ignore
# from flask import jsonify as flask_jsonify  # pyre-ignore
# from flask import request  # pyre-ignore
from karp import schemas
from karp.auth.user import User

# from karp.resourcemgr import entrywrite
# from karp.errors import KarpError
# import karp.auth.auth as auth
# from karp.util import convert
logger = logging.getLogger("karp")
router = APIRouter()

auth_scheme = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    print(f"{credentials!r}")
    return User("dummy", {}, None)


# @auth.auth.authorization("WRITE", add_user=True)


@router.post(
    "/entries/add/<resource_id>/",
    response_model=schemas.EntryCreated,
    status_code=status.HTTP_201_CREATED,
)
def add_entry(
    resource_id: str, entry: schemas.Entry
):  # , user: User = Depends(get_current_user)):
    logger.info("resource_id: %s", resource_id)
    return {"newID": 1}
    # data = request.get_json()
    # new_id = entrywrite.add_entry(
    #     resource_id, data["entry"], user.identifier, message=data.get("message", "")
    # )
    # return flask_jsonify({"newID": new_id}), 201


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
    print("init edit module")
    app.include_router(router, tags=["edit"])
