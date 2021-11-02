"""SQL Resource Repository"""
import logging
import typing
from typing import Dict, List, Optional, Tuple, Union
from uuid import UUID

from sqlalchemy.orm import sessionmaker, Session

from karp.foundation.events import EventBus
from karp.lex.domain import errors, entities
from karp.lex.application import repositories
from karp.lex.domain.errors import IntegrityError, RepositoryStatusError
from karp.lex.domain.entities.resource import Resource, ResourceOp

from karp.db_infrastructure import db
from karp.db_infrastructure.sql_unit_of_work import SqlUnitOfWork
from karp.lex_infrastructure.sql.sql_models import ResourceModel
from karp.db_infrastructure.sql_repository import SqlRepository

_logger = logging.getLogger("karp")


class SqlResourceRepository(SqlRepository, repositories.ResourceRepository):
    def __init__(self, session: db.Session):
        repositories.ResourceRepository.__init__(self)
        SqlRepository.__init__(self, session=session)

    def check_status(self):
        self._check_has_session()
        try:
            self._session.execute("SELECT 1")
        except db.SQLAlchemyError as err:
            _logger.exception(str(err))
            raise errors.RepositoryStatusError("Database error") from err

    @classmethod
    def primary_key(cls):
        return "resource_id"

    def _save(self, resource: Resource):
        self._check_has_session()
        # Check if resource exists
#        existing_resource = self.by_resource_id(resource.resource_id)
#        if (
#            existing_resource
#            and not existing_resource.discarded
#            and existing_resource.id != resource.id
#        ):
#            raise errors.IntegrityError(
#                f"Resource with resource_id '{resource.resource_id}' already exists."
#            )
        if resource.version is None:
            resource._version = self.get_latest_version(
                resource.resource_id) + 1

        # self._session.execute(
        #     db.insert(ResourceModel).values(**self._resource_to_dict(resource))
        # )
        resource_dto = ResourceModel.from_entity(resource)
        self._session.add(resource_dto)

    def resource_ids(self) -> List[str]:
        self._check_has_session()
        query = self._session.query(ResourceModel)
        return [row.resource_id for row in query.group_by(ResourceModel.resource_id).all()]

    def _by_id(
        self, id: Union[UUID, str], *, version: Optional[int] = None
    ) -> typing.Optional[entities.Resource]:
        self._check_has_session()
        query = self._session.query(ResourceModel).filter_by(id=id)
        if version:
            query = query.filter_by(version=version)
        else:
            query = query.order_by(ResourceModel.version.desc())
        resource_dto = query.first()
        return resource_dto.to_entity() if resource_dto else None

    def _by_resource_id(
        self, resource_id: str, *, version: Optional[int] = None
    ) -> Optional[Resource]:
        self._check_has_session()
        query = self._session.query(
            ResourceModel).filter_by(resource_id=resource_id)
        if version:
            query = query.filter_by(version=version)
        else:
            query = query.order_by(ResourceModel.version.desc())
        resource_dto = query.first()
        return resource_dto.to_entity() if resource_dto else None

    def resources_with_id(self, resource_id: str):
        pass

    def resource_with_id_and_version(
        self, resource_id: str, version: int
    ) -> Optional[Resource]:
        self._check_has_session()
        query = self._session.query(ResourceModel)
        resource_dto = query.filter_by(
            resource_id=resource_id, version=version).first()
        return resource_dto.to_entity() if resource_dto else None

    def get_active_resource(self, resource_id: str) -> Optional[Resource]:
        self._check_has_session()
        query = self._session.query(ResourceModel)
        resource_dto = query.filter_by(
            resource_id=resource_id, is_published=True
        ).one_or_none()
        return resource_dto.to_entity()

    def get_latest_version(self, resource_id: str) -> int:
        self._check_has_session()
        row = (
            self._session.query(ResourceModel)
            .order_by(ResourceModel.version.desc())
            .filter_by(resource_id=resource_id)
            .first()
        )
        if row is None:
            return 0
        return row.version

    def history_by_resource_id(self, resource_id: str) -> typing.List[entities.Resource]:
        self._check_has_session()
        query = self._session.query(ResourceModel)
        return [
            resource_dto.to_entity()
            for resource_dto in query.filter_by(resource_id=resource_id)
            .order_by(ResourceModel.version.desc())
            .all()
        ]

    def _get_published_resources(self) -> typing.List[entities.Resource]:
        self._check_has_session()
        subq = (
            self._session.query(
                ResourceModel.resource_id,
                db.func.max(ResourceModel.last_modified).label("maxdate"),
            )
            .group_by(ResourceModel.resource_id)
            .subquery("t2")
        )
        query = self._session.query(ResourceModel).join(
            subq,
            db.and_(
                ResourceModel.resource_id == subq.c.resource_id,
                ResourceModel.last_modified == subq.c.maxdate,
                ResourceModel.is_published == True,
            ),
        )

        return [
            resource_dto.to_entity()
            for resource_dto in query
            if resource_dto is not None
        ]

    def _resource_to_dict(self, resource: Resource) -> typing.Dict:
        return {
            "history_id": None,
            "id": resource.id,
            "resource_id": resource.resource_id,
            "version": resource.version,
            "name": resource.name,
            "config": resource.config,
            "is_published": resource.is_published,
            "last_modified": resource.last_modified,
            "last_modified_by": resource.last_modified_by,
            "message": resource.message,
            "op": resource.op,
            "discarded": resource.discarded,
        }


class SqlResourceUnitOfWork(
    SqlUnitOfWork,
    repositories.ResourceUnitOfWork
):
    def __init__(
        self,
        session_factory: sessionmaker,
        event_bus: EventBus,
    ):
        SqlUnitOfWork.__init__(self)
        repositories.ResourceUnitOfWork.__init__(self, event_bus)
        self.session_factory = session_factory
        self._resources = None

    def __enter__(self):
        self._session = self.session_factory()
        self._resources = SqlResourceRepository(self._session)
        return super().__enter__()

    @property
    def repo(self) -> SqlResourceRepository:
        if self._resources is None:
            raise RuntimeError("No resources")
        return self._resources
    # def _resource_to_row(
    #     self, resource: Resource
    # ) -> Tuple[
    #     None,
    #     UUID,
    #     str,
    #     int,
    #     str,
    #     Dict,
    #     Optional[bool],
    #     float,
    #     str,
    #     str,
    #     ResourceOp,
    #     bool,
    # ]:
    #     # config = resource.config
    #     resource.config["entry_repository_type"] = resource.entry_repository_type
    #     resource.config[
    #         "entry_repository_settings"
    #     ] = resource.entry_repository_settings
    #     return (
    #         None,
    #         resource.id,
    #         resource.resource_id,
    #         resource.version,
    #         resource.name,
    #         resource.config,
    #         resource.is_published,
    #         resource.last_modified,
    #         resource.last_modified_by,
    #         resource.message,
    #         resource.op,
    #         resource.discarded,
    #     )

    # def _row_to_resource(self, row) -> Resource:
    #     entry_repository_type = row.config.pop("entry_repository_type")
    #     entry_respsitory_settings = row.config.pop("entry_repository_settings")
    #     return Resource(
    #         entity_id=row.id,
    #         resource_id=row.resource_id,
    #         version=row.version,
    #         name=row.name,
    #         config=row.config,
    #         message=row.message,
    #         op=row.op,
    #         is_published=row.is_published,
    #         last_modified=row.last_modified,
    #         last_modified_by=row.last_modified_by,
    #         discarded=row.discarded,
    #         entry_repository_type=entry_repository_type,
    #         entry_repository_settings=entry_respsitory_settings,
    #     )
