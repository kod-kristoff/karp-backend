from collections import namedtuple
import logging
from typing import List, Optional, Union
import logging

import sqlalchemy
from sqlalchemy import (
    select,
    Boolean,
    Enum,
    Table,
    Column,
    MetaData,
    String,
    Integer,
    Text,
    create_engine,
    Float,
)
from sqlalchemy.orm import mapper, scoped_session, sessionmaker, composite
import sqlalchemy.exc
import sqlalchemy.orm.exc
from sqlalchemy.sql.schema import UniqueConstraint
from sqlalchemy_utils import UUIDType
from sqlalchemy_json import NestedMutableJson
from sqlalchemy_utils.functions import create_database, drop_database

from karp.errors import IntegrityError
from karp.domain import model
from karp.domain.models.resource import (
    ResourceOp,
)  # Resource, ResourceReporter
from karp.domain.ports import (
    UnitOfWork,
    UnitOfWorkManager,
    ResourceRepository,
)
from karp.utility.unique_id import UniqueId


# pylint: disable=unsubscriptable-object

metadata = MetaData()

logger = logging.getLogger(__name__)

resources = Table(
    "resources",
    metadata,
    Column("history_id", Integer, primary_key=True),
    Column("id", UUIDType, nullable=False),
    Column("machine_name", String(32), nullable=False),
    Column("version", Integer, nullable=False),
    Column("name", String(64), nullable=False),
    Column("config", NestedMutableJson, nullable=False),
    Column("is_published", Boolean, index=True, nullable=True, default=None),
    Column("last_modified", Float, nullable=False),
    Column("last_modified_by", String(100), nullable=False),
    Column("message", String(100), nullable=False),
    Column("op", Enum(ResourceOp), nullable=False),
    # Column("entry_json_schema", Text, nullable=False),
    Column("discarded", Boolean, default=False),
    # Column("reporter_name", String(50)),
    # Column("reporter_email", String(50)),
    # Column("description", Text),
    UniqueConstraint("id", "version", name="resource_version_unique_constraint"),
)


def start_mappers():
    logger.info("Starting mappers")
    mapper(
        model.Resource,
        resources,
        properties={
            "_id": resources.c.id,
            "machine_name": resources.c.machine_name,
            "_version": resources.c.version,
            "_name": resources.c.name,
            "config": resources.c.config,
            "is_published": resources.c.is_published,
            "_last_modified": resources.c.last_modified,
            "_last_modified_by": resources.c.last_modified_by,
            "_message": resources.c.message,
            "_op": resources.c.op,
            # "entry_json_schema": resources.c.entry_json_schema,
            "discarded": resources.c.discarded,
            # "reporter_name": resources.c.reporter_name,
            # "reporter_email": resources.c.reporter_email,
            # "description": resources.c.description,
            # "reporter": composite(
            #     ResourceReporter,
            #     resources.c.reporter_name,
            #     resources.c.reporter_email,
            # ),
        },
    )


class SqlAlchemyUnitOfWorkManager(UnitOfWorkManager):
    def __init__(self, session_maker):
        self.session_maker = session_maker

    def start(self):
        return SqlAlchemyUnitOfWork(self.session_maker)


class SqlResourceRepository(ResourceRepository):
    def __init__(self, session):
        self._session = session

    def put(self, resource: Resource) -> None:
        try:
            self._session.add(resource)
        except sqlalchemy.exc.IntegrityError as err:
            raise IntegrityError(
                f"Resource with id='{resource.id}' or machine_name='{resource.machine_name}' already exists."
            ) from err

    def by_id(
        self, id: Union[UniqueId, str], *, version: Optional[int]
    ) -> Optional[Resource]:
        return super().by_id(id, version=version)

    def by_resource_id(
        self, resource_id: str, *, version: Optional[int]
    ) -> Optional[Resource]:
        return super().by_resource_id(resource_id, version=version)

    def resource_ids(self) -> List[Resource]:
        return super().resource_ids()

    def resource_with_id_and_version(self, resource_id: str, version: int):
        return super().resource_with_id_and_version(resource_id, version)

    def get_active_resource(self, resource_id: str) -> Optional[Resource]:
        return super().get_active_resource(resource_id)

    def resources_with_id(self, resource_id: str):
        return super().resources_with_id(resource_id)

    def get_published_resources(self) -> List[Resource]:
        return super().get_published_resources()


class SqlAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, sessionfactory):
        self.sessionfactory = sessionfactory
        self.session = None

    def __enter__(self):
        self.session = self.sessionfactory()
        return self

    def __exit__(self, type, value, traceback):
        self.session.close()
        self.session = None

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    @property
    def resources(self):
        return SqlResourceRepository(self.session)


class SqlAlchemy:
    resource_mapper = None

    @classmethod
    def set_resource_mapper(cls, resource_mapper):
        cls.resource_mapper = resource_mapper

    def __init__(self, uri):
        self.engine = create_engine(uri)
        self._session_maker = scoped_session(
            sessionmaker(self.engine),
        )
        self.metadata = None

    @property
    def unit_of_work_manager(self):
        return SqlAlchemyUnitOfWorkManager(self._session_maker)

    def recreate_schema(self):
        drop_database(self.engine.url)
        create_database(self.engine.url)
        self.metadata.create_all()

    def get_session(self):
        return self._session_maker()

    def configure_mappings(self):
        self.metadata = MetaData(self.engine)

        # ResourceReporter.__composite_values__ = lambda i: (i.name, i.email)

        if self.resource_mapper is None:
            self.set_resource_mapper(
                mapper(
                    Resource,
                    resources,
                    properties={
                        "_id": resources.c.id,
                        "machine_name": resources.c.machine_name,
                        "_version": resources.c.version,
                        "_name": resources.c.name,
                        "config": resources.c.config,
                        "is_published": resources.c.is_published,
                        "_last_modified": resources.c.last_modified,
                        "_last_modified_by": resources.c.last_modified_by,
                        "_message": resources.c.message,
                        "_op": resources.c.op,
                        # "entry_json_schema": resources.c.entry_json_schema,
                        "discarded": resources.c.discarded,
                        # "reporter_name": resources.c.reporter_name,
                        # "reporter_email": resources.c.reporter_email,
                        # "description": resources.c.description,
                        # "reporter": composite(
                        #     ResourceReporter,
                        #     resources.c.reporter_name,
                        #     resources.c.reporter_email,
                        # ),
                    },
                )
            )


class SqlAlchemySessionContext:
    def __init__(self, session_maker):
        self._session_maker = session_maker
        self._session = None

    def __enter__(self):
        self._session = self._session_maker()

    def __exit__(self, type, value, traceback):
        self._session = None
        self._session_maker.remove()


class ResourceViewBuilder:

    resource_view_model = namedtuple(
        "resource_view",
        [
            "id",
            "machine_name",
            "name",
            "version",
            "config",
            "is_published",
            "last_modified",
            "last_modified_by",
            "message",
            "op",
            "discarded",
        ],
    )

    def __init__(self, session):
        self.session = session

    def fetch(self, _id):
        # return self.session.execute(
        #     "SELECT id, machine_name, name, version, config, is_published, last_modified, last_modified_by, message, op, discarded  "
        #     + " FROM resources "
        #     + " WHERE id = :id",
        #     {"id": _id.bytes},
        # )
        return self.session.query(Resource).filter_by(_id=_id).first()
