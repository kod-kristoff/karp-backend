from karp.domain.models.entry import EntryOp, EntryStatus
from karp.infrastructure.sql import db


class BaseEntry:
    entry_id = db.Column(db.String(100), primary_key=True)
    id = db.Column(db.UUIDType, nullable=False)
    discarded = db.Column(db.Boolean, nullable=False)


class BaseHistoryEntry:
    history_id = db.Column(db.Integer, primary_key=True)
    id = db.Column(db.UUIDType, nullable=False)
    entry_id = db.Column(db.String(100), nullable=False)
    version = db.Column(db.Integer, nullable=False)
    last_modified = db.Column(db.Float, nullable=False)
    last_modified_by = db.Column(db.String(100), nullable=False)
    body = db.Column(db.NestedMutableJson, nullable=False)
    status = db.Column(db.Enum(EntryStatus), nullable=False)
    message = db.Column(db.Text(length=120))
    op = db.Column(db.Enum(EntryOp), nullable=False)
    discarded = db.Column(db.Boolean, default=False)

    @classmethod
    @db.declared_attr
    def __table_args__(cls):
        return db.UniqueConstraint("id", "version", name="id_version_unique_constraint")


class BaseRuntimeEntry:
    entry_id = db.Column(db.String(100), primary_key=True)
    history_id = db.Column(db.Integer, nullable=False)
    id = db.Column(db.UUIDType, nullable=False)
    discarded = db.Column(db.Boolean, nullable=False)


# class Resource(db.Base):
#     pass
