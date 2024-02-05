from typing import Iterable, Optional  # noqa: D100, I001

import sqlalchemy as sa
from sqlalchemy import sql

from karp.lex.application.dtos import ResourceDto
from karp.lex_core.value_objects.unique_id import UniqueId

from karp.lex_infrastructure.sql.sql_models import ResourceModel
from karp.lex_infrastructure.queries.base import SqlQuery


class SqlGetPublishedResources(SqlQuery):  # noqa: D101
    def query(self) -> Iterable[ResourceDto]:  # noqa: D102
        subq = (
            sql.select(
                ResourceModel.entity_id,
                sa.func.max(ResourceModel.last_modified).label("maxdate"),
            )
            .group_by(ResourceModel.entity_id)
            .subquery("t2")
        )

        stmt = sql.select(ResourceModel).join(
            subq,
            sa.and_(
                ResourceModel.entity_id == subq.c.entity_id,
                ResourceModel.last_modified == subq.c.maxdate,
                ResourceModel.is_published == True,  # noqa: E712
            ),
        )
        return (_row_to_dto(row) for row in self._session.connection().execute(stmt))


class SqlGetResources(SqlQuery):  # noqa: D101
    def query(self) -> Iterable[ResourceDto]:  # noqa: D102
        subq = (
            sql.select(
                ResourceModel.entity_id,
                sa.func.max(ResourceModel.last_modified).label("maxdate"),
            )
            .group_by(ResourceModel.entity_id)
            .subquery("t2")
        )

        stmt = sql.select(ResourceModel).join(
            subq,
            sa.and_(
                ResourceModel.entity_id == subq.c.entity_id,
                ResourceModel.last_modified == subq.c.maxdate,
            ),
        )
        return [_row_to_dto(row) for row in self._session.connection().execute(stmt)]


class SqlReadOnlyResourceRepository(SqlQuery):
    def get_by_resource_id(  # noqa: D102
        self, resource_id: str, version: Optional[int] = None
    ) -> Optional[ResourceDto]:
        resource = self._get_by_resource_id(resource_id)
        if not resource:
            return None

        if version is not None:
            resource = self.get_by_id(resource.id, version=version)
        return resource

    def get_by_id(  # noqa: D102
        self, entity_id: UniqueId, version: Optional[int] = None
    ) -> Optional[ResourceDto]:
        filters: dict[str, UniqueId | str | int] = {"entity_id": entity_id}
        if version:
            filters["version"] = version
        stmt = (
            sql.select(ResourceModel)
            .filter_by(**filters)
            .order_by(ResourceModel.last_modified.desc())
        )
        print(f"stmt={stmt!s}")
        row = self._session.connection().execute(stmt).first()

        return _row_to_dto(row) if row else None

    def _get_by_resource_id(self, resource_id: str) -> Optional[ResourceDto]:
        subq = (
            sql.select(
                ResourceModel.entity_id,
                sa.func.max(ResourceModel.last_modified).label("maxdate"),
            )
            .group_by(ResourceModel.entity_id)
            .subquery("t2")
        )

        stmt = sql.select(ResourceModel).join(
            subq,
            sa.and_(
                ResourceModel.entity_id == subq.c.entity_id,
                ResourceModel.last_modified == subq.c.maxdate,
                ResourceModel.resource_id == resource_id,
            ),
        )
        stmt = stmt.order_by(ResourceModel.last_modified.desc())
        row = self._session.connection().execute(stmt).first()

        return _row_to_dto(row) if row else None

    def get_published_resources(self) -> Iterable[ResourceDto]:  # noqa: D102
        subq = (
            sql.select(
                ResourceModel.entity_id,
                sa.func.max(ResourceModel.last_modified).label("maxdate"),
            )
            .group_by(ResourceModel.entity_id)
            .subquery("t2")
        )

        stmt = sql.select(ResourceModel).join(
            subq,
            sa.and_(
                ResourceModel.entity_id == subq.c.entity_id,
                ResourceModel.last_modified == subq.c.maxdate,
                ResourceModel.is_published == True,  # noqa: E712
            ),
        )
        return (_row_to_dto(row) for row in self._session.connection().execute(stmt))

    def get_all_resources(self) -> Iterable[ResourceDto]:  # noqa: D102
        subq = (
            sql.select(
                ResourceModel.entity_id,
                sa.func.max(ResourceModel.last_modified).label("maxdate"),
            )
            .group_by(ResourceModel.entity_id)
            .subquery("t2")
        )

        stmt = sql.select(ResourceModel).join(
            subq,
            sa.and_(
                ResourceModel.entity_id == subq.c.entity_id,
                ResourceModel.last_modified == subq.c.maxdate,
            ),
        )
        return (_row_to_dto(row) for row in self._session.connection().execute(stmt))


def _row_to_dto(row_proxy) -> ResourceDto:
    return ResourceDto(
        id=row_proxy.entity_id,
        resourceId=row_proxy.resource_id,
        version=row_proxy.version,
        config=row_proxy.config,
        isPublished=row_proxy.is_published,
        lastModified=row_proxy.last_modified,
        lastModifiedBy=row_proxy.last_modified_by,
        message=row_proxy.message,
        name=row_proxy.name,
        discarded=row_proxy.discarded,
    )
