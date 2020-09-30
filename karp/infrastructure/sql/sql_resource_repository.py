"""SQL Resource Repository"""
import logging
from typing import Optional, List, Tuple, Dict
from uuid import UUID

from karp.domain.errors import RepositoryStatusError
from karp.domain.models.resource import (
    Resource,
    ResourceOp,
    ResourceRepository,
)

from karp.infrastructure.sql import db, sql_models
from karp.infrastructure.sql.sql_repository import SqlRepository

_logger = logging.getLogger("karp")


class SqlResourceRepository(ResourceRepository, SqlRepository):
    def __init__(self):
        super().__init__()
        self.table = sql_models.ResourceDefinition

    def check_status(self):
        self._check_has_session()
        try:
            self._session.execute("SELECT 1")
        except db.SQLAlchemyError as e:
            _logger.exception(str(e))
            raise RepositoryStatusError()

    def put(self, resource: Resource):
        self._check_has_session()
        if resource.version is None:
            resource._version = self.get_latest_version(resource.resource_id) + 1
        self._session.execute(
            db.insert(self.table, values=self._resource_to_row(resource))
        )

    update = put

    def resource_ids(self) -> List[str]:
        self._check_has_session()
        query = self._session.query(self.table)
        return [
            row.resource_id for row in query.group_by(self.table.resource_id).all()
        ]

    def resources_with_id(self, resource_id: str):
        pass

    def resource_with_id_and_version(
        self, resource_id: str, version: int
    ) -> Optional[Resource]:
        self._check_has_session()
        query = self._session.query(self.table)
        return self._row_to_resource(
            query.filter_by(resource_id=resource_id, version=version).first()
        )

    def get_active_resource(self, resource_id: str) -> Optional[Resource]:
        self._check_has_session()
        query = self._session.query(self.table)
        return self._row_to_resource(
            query.filter_by(resource_id=resource_id, is_published=True).one_or_none()
        )

    def get_latest_version(self, resource_id: str) -> int:
        self._check_has_session()
        row = (
            self._session.query(self.table)
            .order_by(self.table.version.desc())
            .filter_by(resource_id=resource_id)
            .first()
        )
        if row is None:
            return 0
        return row.version

    def history_by_resource_id(self, resource_id: str) -> List:
        self._check_has_session()
        query = self._session.query(self.table)
        return [
            self._row_to_resource(row)
            for row in query.filter_by(resource_id=resource_id).all()
        ]

    def get_published_resources(self) -> List[Resource]:
        self._check_has_session()
        subq = (
            self._session.query(
                self.table.resource_id,
                db.func.max(self.table.last_modified).label("maxdate"),
            )
            .group_by(self.table.resource_id)
            .subquery("t2")
        )
        query = self._session.query(self.table).join(
            subq,
            db.and_(
                self.table.resource_id == subq.c.resource_id,
                self.table.last_modified == subq.c.maxdate,
                self.table.is_published == True,
            ),
        )

        return [self._row_to_resource(row) for row in query if row is not None]

    def _resource_to_row(
        self, resource: Resource
    ) -> Tuple[
        None, UUID, str, int, str, Dict, Optional[bool], float, str, str, ResourceOp, bool
    ]:
        return (
            None,
            resource.id,
            resource.resource_id,
            resource.version,
            resource.name,
            resource.config,
            resource.is_published,
            resource.last_modified,
            resource.last_modified_by,
            resource.message,
            resource.op,
            resource.discarded,
        )

    def _row_to_resource(self, row) -> Optional[Resource]:
        return (
            Resource(
                entity_id=row.id,
                resource_id=row.resource_id,
                version=row.version,
                name=row.name,
                config=row.config,
                message=row.message,
                op=row.op,
                is_published=row.is_published,
                last_modified=row.last_modified,
                last_modified_by=row.last_modified_by,
                discarded=row.discarded,
            )
            if row
            else None
        )

