from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from karp.fastapi_app.utilities import get_db
from karp import crud, schemas

router = APIRouter()


@router.get("/resources", response_model=List[schemas.Resource])
def get_resources(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_resources(db, skip=skip, limit=limit)


def init_app(app):
    app.include_router(router)
