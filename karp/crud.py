from typing import Optional

from karp.models import ResourceDefinition


def get_latest_resource_definition(id: str) -> Optional[ResourceDefinition]:
    return (
        ResourceDefinition.query.filter_by(resource_id=id)
        .order_by(ResourceDefinition.version.desc())
        .first()
    )


def get_resource_definition(id: str, version: int) -> Optional[ResourceDefinition]:
    return ResourceDefinition.query.filter_by(resource_id=id, version=version).first()


def get_active_resource_definition(id: str) -> Optional[ResourceDefinition]:
    return ResourceDefinition.query.filter_by(resource_id=id, active=True).first()


def get_active_or_latest_resource_definition(id: str) -> Optional[ResourceDefinition]:
    rd = get_active_resource_definition(id)
    if not rd:
        rd = get_latest_resource_definition(id)
    return rd


def get_next_resource_version(id: str) -> int:
    latest_resource = get_latest_resource_definition(id)

    if latest_resource:
        return latest_resource.version + 1
    else:
        return 1
