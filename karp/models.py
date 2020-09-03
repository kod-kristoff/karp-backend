from typing import Any, Dict
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declared_attr  # pyre-ignore
from sqlalchemy.sql import func  # pyre-ignore
from sqlalchemy_utils import UUIDType
from sqlalchemy_json import JSON

from karp.database import Base, engine


class Resource(Base):
    __tablename__ = "resources"
    id = sa.Column(UUIDType(), primary_key=True)
    resource_id = sa.Column(sa.String(30), nullable=False)
    version = sa.Column(sa.Integer, nullable=False)
    timestamp = sa.Column(sa.Float(), nullable=False, server_default=func.now())
    config_file = sa.Column(JSON(), nullable=False)
    entry_json_schema = sa.Column(JSON(), nullable=False)
    active = sa.Column(sa.Boolean, default=False)
    deleted = sa.Column(sa.Boolean, default=False)
    __table_args__ = (
        sa.UniqueConstraint(
            "resource_id", "version", name="resource_version_unique_constraint"
        ),
        # TODO only one resource can be active, but several can be inactive
        #    here is how to do it in MariaDB, unclear whether this is possible using SQLAlchemy
        #    `virtual_column` char(0) as (if(active,'', NULL)) persistent
        #    and
        #    UNIQUE KEY `resource_version_unique_active` (`resource_id`,`virtual_column`)
        #    this works because the tuple (saldo, NULL) is not equal to (saldo, NULL)
    )

    def __repr__(self):
        return """<Resource(resource_id='{}',
                            version='{}',
                            timestamp='{}',
                            active='{}',
                            deleted='{}')
                >""".format(
            self.resource_id, self.version, self.timestamp, self.active, self.deleted
        )


class BaseEntry:
    id = sa.Column(sa.Integer, primary_key=True)
    body = sa.Column(sa.Text, nullable=False)
    deleted = sa.Column(sa.Boolean, default=False)


# class DummyEntry(Base, BaseEntry):
#     """
#     This table is created so that Alembic can help us autodetect what changes have been made to
#     the concrete resource tables (s.a. places_1)
#     """

#     pass


class BaseHistory:
    id = sa.Column(sa.Integer, primary_key=True)
    entry_id = sa.Column(sa.String, nullable=False)
    user_id = sa.Column(sa.Text, nullable=False)
    timestamp = sa.Column(sa.Integer, nullable=False)
    body = sa.Column(sa.Text)
    op = sa.Column(sa.Enum("ADD", "DELETE", "UPDATE"), nullable=False)
    version = sa.Column(sa.Integer, nullable=False)
    message = sa.Column(sa.Text)

    @declared_attr
    def __table_args__(cls):
        return (
            sa.UniqueConstraint(
                "entry_id", "version", name="entry_id_version_unique_constraint"
            ),
        )


# class DummyHistoryEntry(Base, BaseHistory):
#     """
#     This table is created so that Alembic can help us autodetect what changes have been made to
#     the concrete resource history tables (s.a. places_1_history)
#     """

#     pass


_class_cache: Dict[str, Any] = {}


def create_history_model(resource_id: str, version: int):
    # resource_table_name = resource_id + "_" + str(version)
    history_table_name = resource_id + "_history"

    history_model = _class_cache.get(history_table_name)
    if history_model:
        return history_model

    # foreign_key_constraint = sa.ForeignKeyConstraint(
    #     ("entry_id",), (resource_table_name + ".id",)
    # )

    attributes = {
        "__tablename__": history_table_name,
        "__table_args__": BaseHistory.__table_args__,
    }

    history_model = type(
        history_table_name,
        (
            Base,
            BaseHistory,
        ),
        attributes,
    )
    _class_cache[history_table_name] = history_model

    return history_model


def get_or_create_resource_model(config, version):
    resource_id = config["resource_id"]
    table_name = f"{resource_id}_{version}_runtime"
    history_table_name = f"{resource_id}_history"
    if table_name in _class_cache:
        return _class_cache[table_name]
    else:
        if engine.driver == "pysqlite":
            ref_column = sa.Unicode(100)
        else:
            ref_column = sa.Unicode(100, collation="utf8_bin")
        attributes = {
            "__tablename__": table_name,
            "__table_args__": (
                sa.UniqueConstraint("entry_id", name="entry_id_unique_constraint"),
            ),
            "entry_id": sa.Column(ref_column, nullable=False),
            "history_id": sa.Column(
                sa.Integer(), sa.ForeignKey(f"{history_table_name}.id")
            ),
        }

        child_tables = {}
        for field_name in config.get("referenceable", ()):
            field = config["fields"][field_name]
            # TODO check if field is nullable

            if not field.get("collection"):
                if field["type"] == "integer":
                    column_type = sa.Integer()
                elif field["type"] == "number":
                    column_type = sa.Float()
                elif field["type"] == "string":
                    column_type = ref_column
                else:
                    raise NotImplementedError()
                attributes[field_name] = sa.Column(column_type)
            else:
                child_table_name = table_name + "_" + field_name
                attributes[field_name] = sa.relationship(
                    child_table_name,
                    backref=table_name,
                    cascade="save-update, merge,delete, delete-orphan",
                )
                child_attributes = {
                    "__tablename__": child_table_name,
                    "__table_args__": (
                        sa.PrimaryKeyConstraint("entry_id", field_name),
                    ),
                    "entry_id": sa.Column(
                        sa.Integer, sa.ForeignKey(table_name + ".id")
                    ),
                }
                if field["type"] == "object":
                    raise ValueError("not possible to reference lists of objects")
                if field["type"] == "integer":
                    child_db_column_type = sa.Integer()
                elif field["type"] == "number":
                    child_db_column_type = sa.Float()
                elif field["type"] == "string":
                    child_db_column_type = ref_column
                else:
                    raise NotImplementedError()
                child_attributes[field_name] = sa.Column(child_db_column_type)
                child_class = type(child_table_name, (Base,), child_attributes)
                child_tables[field_name] = child_class

        sqlalchemy_class = type(
            resource_id,
            (
                Base,
                BaseEntry,
            ),
            attributes,
        )
        sqlalchemy_class.child_tables = child_tables

        _class_cache[table_name] = sqlalchemy_class
        return sqlalchemy_class
