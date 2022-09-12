import logging
from typing import Optional

from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    Response,
    Security,
    status,
    Path,
    Query,
)
import pydantic
from starlette import responses

from karp import errors as karp_errors, auth, lex, search
from karp.foundation.commands import CommandBus
from karp.lex.application.queries import EntryDto, GetEntryHistory
from karp.lex.domain import commands, errors
from karp.auth import User
from karp.foundation.value_objects import PermissionLevel
from karp.auth import AuthService
from karp.webapp import schemas, dependencies as deps, services


router = APIRouter()

logger = logging.getLogger(__name__)


@router.get("/{resource_id}/{entry_id:path}", response_model=EntryDto, tags=["History"])
def get_history_for_entry(
    resource_id: str,
    entry_id: str,
    version: Optional[int] = Query(None),
    user: auth.User = Security(deps.get_user, scopes=["admin"]),
    auth_service: auth.AuthService = Depends(deps.get_auth_service),
    get_entry_history: GetEntryHistory = Depends(deps.get_entry_history),
):
    services.authorize_user(
        auth_service,
        user,
        level=PermissionLevel.admin,
        resource_ids=[resource_id],
    )

    logger.info(
        "getting history for entry",
        extra={
            "resource_id": resource_id,
            "entry_id": entry_id,
            "user": user.identifier,
        },
    )
    historical_entry = get_entry_history.query(resource_id, entry_id, version=version)

    return historical_entry


@router.post(
    "/{resource_id}/add", status_code=status.HTTP_201_CREATED, tags=["Editing"]
)
@router.put("/{resource_id}", status_code=status.HTTP_201_CREATED, tags=["Editing"])
def add_entry(
    resource_id: str,
    data: schemas.EntryAdd,
    user: User = Security(deps.get_user, scopes=["write"]),
    auth_service: AuthService = Depends(deps.get_auth_service),
    adding_entry_uc: lex.AddingEntry = Depends(deps.get_lex_uc(lex.AddingEntry)),
):

    services.authorize_user(
        auth_service, user, level=PermissionLevel.write, resource_ids=[resource_id]
    )

    logger.info("adding entry", extra={"resource_id": resource_id, "data": data})
    try:
        new_entry = adding_entry_uc.execute(
            commands.AddEntry(
                resource_id=resource_id,
                user=user.identifier,
                message=data.message,
                entry=data.entry,
            )
        )
    except errors.IntegrityError as exc:
        return responses.JSONResponse(
            status_code=400,
            content={
                "error": str(exc),
                "errorCode": karp_errors.ClientErrorCodes.DB_INTEGRITY_ERROR,
            },
        )
    except errors.InvalidEntry as exc:
        return responses.JSONResponse(
            status_code=400,
            content={
                "error": str(exc),
                "errorCode": karp_errors.ClientErrorCodes.ENTRY_NOT_VALID,
            },
        )

    return {"newID": new_entry.entry_id, "entityID": new_entry.entity_id}


@router.post("/{resource_id}/preview")
def preview_entry(
    resource_id: str,
    data: schemas.EntryAdd,
    user: auth.User = Security(deps.get_user_optional, scopes=["read"]),
    auth_service: auth.AuthService = Depends(deps.get_auth_service),
    preview_entry: search.PreviewEntry = Depends(
        deps.inject_from_req(search.PreviewEntry)
    ),
):
    services.authorize_user(
        auth_service, user, level=PermissionLevel.read, resource_ids=[resource_id]
    )

    try:
        input_dto = search.PreviewEntryInputDto(
            resource_id=resource_id, entry=data.entry, user=user.identifier
        )
    except pydantic.ValidationError as err:
        logger.exception("data is not valid")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail={"error": str(err)}
        )
    else:
        return preview_entry.query(input_dto)


# @router.post("/{resource_id}/{entry_id}/update", tags=["Editing"])
@router.post("/{resource_id}/{entry_id:path}", tags=["Editing"])
def update_entry(
    response: Response,
    resource_id: str,
    entry_id: str,
    data: schemas.EntryUpdate,
    user: User = Security(deps.get_user, scopes=["write"]),
    auth_service: AuthService = Depends(deps.get_auth_service),
    bus: CommandBus = Depends(deps.inject_from_req(CommandBus)),
):
    services.authorize_user(
        auth_service, user, level=PermissionLevel.write, resource_ids=[resource_id]
    )

    #     force_update = convert.str2bool(request.args.get("force", "false"))
    #     data = request.get_json()
    #     version = data.get("version")
    #     entry = data.get("entry")
    #     message = data.get("message")
    #     if not (version and entry and message):
    #         raise KarpError("Missing version, entry or message")
    logger.info(
        "updating entry",
        extra={
            "resource_id": resource_id,
            "entry_id": entry_id,
            "data": data,
            "user": user.identifier,
        },
    )
    try:
        entry = bus.dispatch(
            commands.UpdateEntry(
                resource_id=resource_id,
                entry_id=entry_id,
                version=data.version,
                user=user.identifier,
                message=data.message,
                entry=data.entry,
            )
        )
        # new_entry = entries.add_entry(
        #     resource_id, data.entry, user.identifier, message=data.message
        # )
        # new_id = entries.update_entry(
        #     resource_id,
        #     entry_id,
        #     data.version,
        #     data.entry,
        #     user.identifier,
        #     message=data.message,
        #     # force=force_update,
        # )
        return {"newID": entry.entry_id, "entityID": entry.entity_id}
    except errors.EntryNotFound:
        return responses.JSONResponse(
            status_code=404,
            content={
                "error": f"Entry '{entry_id}' not found in resource '{resource_id}' (version=latest)",
                "errorCode": karp_errors.ClientErrorCodes.ENTRY_NOT_FOUND,
                "resource": resource_id,
                "entry_id": entry_id,
            },
        )
    except errors.UpdateConflict as err:
        response.status_code = status.HTTP_400_BAD_REQUEST
        err.error_obj["errorCode"] = karp_errors.ClientErrorCodes.VERSION_CONFLICT
        return err.error_obj
    except Exception as err:
        logger.exception(
            "error occured",
            extra={"resource_id": resource_id, "entry_id": entry_id, "data": data},
        )
        raise


@router.delete(
    "/{resource_id}/{entry_id}/delete",
    tags=["Editing"],
    status_code=status.HTTP_204_NO_CONTENT,
)
@router.delete(
    "/{resource_id}/{entry_id}",
    tags=["Editing"],
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_entry(
    resource_id: str,
    entry_id: str,
    user: User = Security(deps.get_user, scopes=["write"]),
    auth_service: AuthService = Depends(deps.get_auth_service),
    deleting_entry_uc: lex.DeletingEntry = Depends(deps.get_lex_uc(lex.DeletingEntry)),
):
    """Delete a entry from a resource."""
    services.authorize_user(
        auth_service, user, level=PermissionLevel.write, resource_ids=[resource_id]
    )
    try:
        deleting_entry_uc.execute(
            commands.DeleteEntry(
                resource_id=resource_id,
                entry_id=entry_id,
                user=user.identifier,
            )
        )
    except errors.EntryNotFound:
        return responses.JSONResponse(
            status_code=404,
            content={
                "error": f"Entry '{entry_id}' not found in resource '{resource_id}' (version=latest)",
                "errorCode": karp_errors.ClientErrorCodes.ENTRY_NOT_FOUND,
                "resource": resource_id,
                "entry_id": entry_id,
            },
        )
    return


def init_app(app):
    app.include_router(router)
