"""Database access"""
import logging
from typing import Dict, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from pydantic import BaseModel

from karp import models

logger = logging.getLogger("karp")


class SystemResponse(BaseModel):
    message: str = "ok"

    def __bool__(self):
        return True


class SystemOk(SystemResponse):
    pass


class SystemNotOk(SystemResponse):
    def __bool__(self):
        return False


def check_database_status(db: Session) -> SystemResponse:
    try:
        db.execute("SELECT 1")
        return SystemOk()
    except SQLAlchemyError as e:
        logger.exception(e)
        return SystemNotOk(message=str(e))


def get_latest_resource_by_resource_id(
    db: Session, resource_id: str
) -> Optional[models.Resource]:
    return (
        db.query(models.Resource)
        .filter_by(resource_id=resource_id)
        .order_by(models.Resource.version.desc())
        .first()
    )


def get_resource_by_resource_id_and_version(
    db: Session, resource_id: str, version: int
) -> Optional[models.Resource]:
    return (
        db.query(models.Resource)
        .filter_by(resource_id=resource_id, version=version)
        .first()
    )


def get_active_resource_definition(
    db: Session, resource_id: str
) -> Optional[models.Resource]:
    return (
        db.query(models.Resource)
        .filter_by(resource_id=resource_id, active=True)
        .first()
    )


def get_active_or_latest_resource_definition(
    db: Session, resource_id: str
) -> Optional[models.Resource]:
    rd = get_active_resource_definition(db, resource_id)
    if not rd:
        rd = get_latest_resource_by_resource_id(db, resource_id)
    return rd


def get_next_resource_version(db: Session, resource_id: str) -> int:
    latest_resource = get_latest_resource_by_resource_id(db, resource_id)

    if latest_resource:
        return latest_resource.version + 1
    else:
        return 1


def get_resources(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Resource).offset(skip).limit(limit).all()
