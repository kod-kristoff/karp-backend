"""Entry repository for use with karp legacy sql format."""
import datetime
import enum
from typing import Dict, List, Optional, Tuple
import uuid

from karp.domain.errors import EntryNotFound
from karp.domain.model.entry_repository import EntryRepository
from karp.domain.model.entry import Entry, EntryOp, EntryStatus
from karp.domain.model.resource import ResourceOp

from karp.infrastructure.sql import db
from karp.infrastructure.sql.sql_repository import SqlRepository
from karp.utility import unique_id


class LegacyEntryOp(enum.Enum):
    ADDED = "added"
    CHANGED = "changed"
    REMOVED = "removed"
    IMPORTED = "imported"


def to_entry_op(op: LegacyEntryOp) -> EntryOp:
    if op == LegacyEntryOp.ADDED:
        return EntryOp.ADDED
    if op == LegacyEntryOp.CHANGED:
        return EntryOp.UPDATED
    if op == LegacyEntryOp.REMOVED:
        return EntryOp.DELETED
    return EntryOp.ADDED


def to_legacy_entry_op(op: EntryOp) -> LegacyEntryOp:
    if op == EntryOp.ADDED:
        return LegacyEntryOp.ADDED
    if op == EntryOp.DELETED:
        return LegacyEntryOp.REMOVED
    if op == EntryOp.UPDATED:
        return LegacyEntryOp.CHANGED
    return LegacyEntryOp.IMPORTED


class SqlLegacyEntryRepository(
    EntryRepository, SqlRepository, repository_type="sql_legacy_v1"
):
    def __init__(
        self,
        *,
        config: Dict[str, str],
        history_table: db.Table,
        runtime_table: db.Table,
        **kwargs,
    ):
        EntryRepository.__init__(self, config=config, **kwargs)
        SqlRepository.__init__(self, db_uri=config["db_uri"])
        self.history_table = history_table
        self.runtime_table = runtime_table

    @classmethod
    def from_dict(cls, settings: Dict):
        db_uri = settings["db_uri"]
        table_name = settings["table_name"]
        lexicon_id = settings["lexicon_id"]
        history_table = db.get_table(db_uri, table_name)
        if history_table is None:
            history_table = create_history_table(db_uri, table_name)
        runtime_table_name = f"runtime_{table_name}_{lexicon_id}"
        runtime_table = db.get_table(db_uri, runtime_table_name)
        if runtime_table is None:
            runtime_table = create_runtime_table(
                db_uri, runtime_table_name, history_table
            )
        resource_id = settings.pop("resource_id")
        resource_name = settings.pop("resource_name", resource_id)
        return cls(
            resource_id=resource_id,
            name=resource_name,
            entity_id=unique_id.make_unique_id(),
            config=settings,
            message=f"LegacyEntryRepository '{resource_id}' created.",
            op=ResourceOp.ADDED,
            version=1,
            history_table=history_table,
            runtime_table=runtime_table,
        )

    @classmethod
    def _create_repository_settings(cls, resource_id: str) -> Dict:
        return {"db_uri": None, "table_name": "karpentry", "lexicon_id": resource_id}

    @property
    def lexicon_id(self) -> str:
        """The lexicon_id for this repository."""
        return self.config["lexicon_id"]

    def put(self, entry: Entry):
        self._check_has_session()
        ins_stmt = db.insert(
            self.history_table, values=self._entry_to_history_row(entry)
        )
        result = self._session.execute(ins_stmt)
        print(f"history_table result: {result}")

        updt_stmt = db.insert(self.runtime_table)
        updt_stmt = updt_stmt.values(self._entry_to_runtime_row(entry))

        result = self._session.execute(updt_stmt)
        print(f"runtime_table result: {result}")

    def update(self, entry: Entry):
        self._check_has_session()
        ins_stmt = db.insert(
            self.history_table, values=self._entry_to_history_row(entry)
        )
        result = self._session.execute(ins_stmt)
        print(f"history_table result: {result}")

        updt_stmt = db.update(self.runtime_table)
        updt_stmt = updt_stmt.where(self.runtime_table.c.entry_id == entry.entry_id)
        updt_stmt = updt_stmt.values(self._entry_to_runtime_row(entry))

        result = self._session.execute(updt_stmt)
        print(f"runtime_table result: {result}")

    def by_entry_id(self, entry_id: str) -> Optional[Entry]:
        pass

    def by_id(self, id: unique_id.UniqueId) -> Optional[Entry]:
        self._check_has_session()
        runtime_query = self._session.query(self.runtime_table)
        runtime_entry = runtime_query.filter_by(id=str(id)).first()
        if runtime_entry is None:
            raise EntryNotFound(f"Entry with id='{id}' not found.")
        query = self._session.query(self.history_table)
        return self._history_row_to_optional_entry(
            query.filter_by(id=str(id), date=runtime_entry.date).first(),
            entry_id=runtime_entry.entry_id,
            status=runtime_entry.status,
        )

    def entry_ids(self) -> List[str]:
        self._check_has_session()
        query = self._session.query(self.runtime_table)
        return [row.entry_id for row in query.filter_by(discarded=False).all()]

    def _entry_to_history_row(
        self, entry: Entry
    ) -> Tuple[str, datetime.datetime, str, Dict, str, str, LegacyEntryOp, int]:
        return (
            str(entry.id),
            datetime.datetime.fromtimestamp(entry.last_modified),
            entry.last_modified_by,
            entry.body,
            entry.message,
            self.lexicon_id,
            to_legacy_entry_op(entry.op),
            -1,
        )

    def _entry_to_runtime_row(self, entry: Entry):
        return (
            entry.entry_id,
            str(entry.id),
            datetime.datetime.fromtimestamp(entry.last_modified),
            entry.discarded,
        )

    def _history_row_to_optional_entry(
        self, row, entry_id: str, status: EntryStatus
    ) -> Optional[Entry]:
        if row:
            return self._history_row_to_entry(row, entry_id=entry_id, status=status)
        return None

    def _history_row_to_entry(self, row, entry_id: str, status: EntryStatus) -> Entry:
        return Entry(
            entity_id=uuid.UUID(row.id, version=4),
            entry_id=entry_id,
            body=row.source,
            last_modified=row.date,
            last_modified_by=row.user,
            message=row.msg,
            op=to_entry_op(row.status),
            status=status,
        )


def create_history_table(db_uri: str, table_name: str) -> db.Table:
    table = db.Table(
        table_name,
        db.metadata(db_uri),
        db.Column("id", db.String(50), index=True),
        db.Column("date", db.DateTime, index=True),
        db.Column("user", db.String(320), index=True),
        # Text(2**24-1) corresponds to MediumText in MySQL
        # avoid using the type MediumText (specific to MySQL)
        db.Column("source", db.NestedMutableJson),
        db.Column("msg", db.String(160)),
        db.Column("lexicon", db.String(50), index=True),
        db.Column("status", db.Enum(LegacyEntryOp)),
        db.Column("version", db.Integer),
    )
    # db.Index("historyindex", db_entry.c.lexicon, db_entry.c.status, db_entry.c.date)
    table.create(db.get_engine(db_uri))
    return table


def create_runtime_table(
    db_uri: str, table_name: str, history_table: db.Table
) -> db.Table:
    table = db.Table(
        table_name,
        db.metadata(db_uri),
        db.Column("entry_id", db.Text(100), primary_key=True),
        db.Column("id", db.UUIDType, db.ForeignKey(history_table.c.id)),
        db.Column("date", db.DateTime, db.ForeignKey(history_table.c.date)),
        db.Column("discarded", db.Boolean),
        db.Column("status", db.Enum(EntryStatus)),
    )
    table.create(db.get_engine(db_uri))
    return table
