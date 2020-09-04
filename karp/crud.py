from typing import Optional

from sqlalchemy.orm import Session

from karp import models


def get_latest_resource_definition(
    db: Session, id: str
) -> Optional[models.ResourceDefinition]:
    return (
        db.query(models.ResourceDefinition)
        .filter_by(resource_id=id)
        .order_by(models.ResourceDefinition.version.desc())
        .first()
    )


def get_resource_definition(
    db: Session, id: str, version: int
) -> Optional[models.ResourceDefinition]:
    return (
        db.query(models.ResourceDefinition)
        .filter_by(resource_id=id, version=version)
        .first()
    )


def get_active_resource_definition(
    db: Session, id: str
) -> Optional[models.ResourceDefinition]:
    return (
        db.query(models.ResourceDefinition)
        .filter_by(resource_id=id, active=True)
        .first()
    )


def get_active_or_latest_resource_definition(
    db: Session, id: str
) -> Optional[models.ResourceDefinition]:
    rd = get_active_resource_definition(db, id)
    if not rd:
        rd = get_latest_resource_definition(db, id)
    return rd


def get_next_resource_version(db: Session, id: str) -> int:
    latest_resource = get_latest_resource_definition(db, id)

    if latest_resource:
        return latest_resource.version + 1
    else:
        return 1
