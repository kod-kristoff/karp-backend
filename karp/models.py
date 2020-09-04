import sqlalchemy as db
from sqlalchemy.ext.declarative import declared_attr  # pyre-ignore
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func  # pyre-ignore


from karp.database import Base, engine


class ResourceDefinition(Base):
    __tablename__ = "resources"
    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.String(30), nullable=False)
    version = db.Column(db.Integer)
    timestamp = db.Column(db.Float, nullable=False, server_default=func.now())
    config_file = db.Column(db.Text, nullable=False)
    entry_json_schema = db.Column(db.Text, nullable=False)
    active = db.Column(db.Boolean, default=False)
    deleted = db.Column(db.Boolean, default=False)
    __table_args__ = (
        db.UniqueConstraint(
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
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    deleted = db.Column(db.Boolean, default=False)


class DummyEntry(Base, BaseEntry):
    """
    This table is created so that Alembic can help us autodetect what changes have been made to
    the concrete resource tables (s.a. places_1)
    """

    __tablename__ = "dummy_entry"


class BaseHistory:
    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.Float, nullable=False)
    body = db.Column(db.Text)
    op = db.Column(db.Enum("ADD", "DELETE", "UPDATE"), nullable=False)
    version = db.Column(db.Integer, nullable=False)
    message = db.Column(db.Text)

    @declared_attr
    def __table_args__(cls):
        return (
            db.UniqueConstraint(
                "entry_id", "version", name="entry_id_version_unique_constraint"
            ),
        )


class DummyHistory(Base, BaseHistory):
    """
    This table is created so that Alembic can help us autodetect what changes have been made to
    the concrete resource history tables (s.a. places_1_history)
    """

    __tablename__ = "dummy_history"


def get_or_create_history_model(resource_id, version):
    resource_table_name = resource_id + "_" + str(version)
    history_table_name = resource_table_name + "_history"

    if history_table_name in class_cache:
        return class_cache[history_table_name]

    foreign_key_constraint = db.ForeignKeyConstraint(
        ("entry_id",), (resource_table_name + ".id",)
    )

    attributes = {
        "__tablename__": history_table_name,
        "__table_args__": (foreign_key_constraint,) + BaseHistory.__table_args__,
    }

    sqlalchemy_class = type(
        history_table_name,
        (
            Base,
            BaseHistory,
        ),
        attributes,
    )
    class_cache[history_table_name] = sqlalchemy_class

    return sqlalchemy_class


class_cache = {}


def get_or_create_resource_model(config, version):
    resource_id = config["resource_id"]
    table_name = resource_id + "_" + str(version)
    if table_name in class_cache:
        return class_cache[table_name]
    else:
        if engine.driver == "pysqlite":
            ref_column = db.Unicode(100)
        else:
            ref_column = db.Unicode(100, collation="utf8_bin")
        attributes = {
            "__tablename__": table_name,
            "__table_args__": (
                db.UniqueConstraint("entry_id", name="entry_id_unique_constraint"),
            ),
            "entry_id": db.Column(ref_column, nullable=False),
        }

        child_tables = {}
        for field_name in config.get("referenceable", ()):
            field = config["fields"][field_name]
            # TODO check if field is nullable

            if not field.get("collection"):
                if field["type"] == "integer":
                    column_type = db.Integer()
                elif field["type"] == "number":
                    column_type = db.Float()
                elif field["type"] == "string":
                    column_type = ref_column
                else:
                    raise NotImplementedError()
                attributes[field_name] = db.Column(column_type)
            else:
                child_table_name = table_name + "_" + field_name
                attributes[field_name] = relationship(
                    child_table_name,
                    backref=table_name,
                    cascade="save-update, merge,delete, delete-orphan",
                )
                child_attributes = {
                    "__tablename__": child_table_name,
                    "__table_args__": (
                        db.PrimaryKeyConstraint("entry_id", field_name),
                    ),
                    "entry_id": db.Column(
                        db.Integer, db.ForeignKey(table_name + ".id")
                    ),
                }
                if field["type"] == "object":
                    raise ValueError("not possible to reference lists of objects")
                if field["type"] == "integer":
                    child_db_column_type = db.Integer()
                elif field["type"] == "number":
                    child_db_column_type = db.Float()
                elif field["type"] == "string":
                    child_db_column_type = ref_column
                else:
                    raise NotImplementedError()
                child_attributes[field_name] = db.Column(child_db_column_type)
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

        class_cache[table_name] = sqlalchemy_class
        return sqlalchemy_class
