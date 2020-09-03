import json
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from karp.fastapi_app.utilities import get_db
from karp import crud, schemas

# from flask import Blueprint  # pyre-ignore
# from flask import jsonify as flask_jsonify  # pyre-ignore

# import karp.resourcemgr as resourcemgr

router = APIRouter()


@router.get("/resources", response_model=List[schemas.ResourceOut])
def get_resources(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    resources = crud.get_resources(db, skip=skip, limit=limit)
    result = []
    for resource in resources:
        resource_obj = {"resource_id": resource.resource_id}

        config_file = json.loads(resource.config_file)
        protected_conf = config_file.get("protected")
        if not protected_conf:
            protected = None
        elif protected_conf.get("admin"):
            protected = "ADMIN"
        elif protected_conf.get("write"):
            protected = "WRITE"
        else:
            protected = "READ"

        if protected:
            resource_obj["protected"] = protected
        result.append(resource_obj)

    return result


def init_app(app):
    app.include_router(router, tags=["config"])
