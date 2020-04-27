"""SQL repository for entries."""
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from karp.domain.model.entry import Entry, EntryOp, Repository as EntryRepository

from karp.infrastructure.sql import db
from karp.infrastructure.sql.sql_repository import SqlRepository


class SqlEntryRepository(EntryRepository, SqlRepository):
    def __init__(self, db_uri: str, table: db.Table, mapped_class: Any):
        super().__init__(db_uri)
        self.table = table
        self.mapped_class = mapped_class

    def put(self, entry: Entry):
        self._check_has_session()
        ins_stmt = db.insert(self.table)
        ins_stmt.values(self._entry_to_row(entry))
        self._session.execute(ins_stmt)
        # self._session.add(
        #     self._entry_to_row(entry)
        #     # self.mapped_class(
        #     #     entry.entry_id,
        #     #     entry.body,
        #     #     entry.id,
        #     #     entry.last_modified,
        #     #     entry.last_modified_by,
        #     #     entry.op,
        #     #     entry.message,
        #     # )
        # )

    def entry_ids(self) -> List[str]:
        self._check_has_session()
        query = self._session.query(self.mapped_class._entry_id)
        return [
            row._entry_id for row in query.group_by(self.mapped_class._entry_id).all()
        ]

    def by_entry_id(self, entry_id: str) -> Optional[Entry]:
        self._check_has_session()
        query = self._session.query(self.mapped_class)
        return (
            query.filter_by(_entry_id=entry_id)
            .order_by(self.mapped_class._version.desc())
            .first()
        )

    def by_id(self, id: str) -> Optional[Entry]:
        self._check_has_session()
        query = self._session.query(self.mapped_class)
        return (
            query.filter_by(_id=id).order_by(self.mapped_class._version.desc()).first()
        )

    def history_by_entry_id(self, entry_id: str) -> List[Entry]:
        self._check_has_session()
        query = self._session.query(self.mapped_class)
        return query.filter_by(_entry_id=entry_id).all()

    def _entry_to_row(
        self, entry: Entry
    ) -> Tuple[None, UUID, str, str, int, Dict, int, str, EntryOp]:
        return (
            None,
            entry.id,
            entry.entry_id,
            entry.last_modified_by,
            int(entry.last_modified),
            entry.body,
            entry.version,
            entry.message,
            entry.op,
        )


def create_repository(db_uri: str, table_name: str) -> SqlEntryRepository:
    table = db.get_table(table_name)
    if not table:
        table = create_entry_table(table_name, db_uri)

    mapped_class = db.map_class_to_some_table(
        Entry,
        table,
        f"Entry_{table_name}",
        properties={
            "_id": table.c.id,
            "_version": table.c.version,
            "_entry_id": table.c.entry_id,
            "_last_modified_by": table.c.user_id,
            "_last_modified": table.c.timestamp,
            "_body": table.c.body,
            "_message": table.c.message,
            "_op": table.c.op,
        },
    )
    return SqlEntryRepository(db_uri, table, mapped_class)


_use_aliased = False


def create_entry_table(table_name: str, db_uri: str) -> db.Table:
    global _use_aliased
    table = db.Table(
        table_name,
        db.metadata(db_uri),
        db.Column("history_id", db.Integer, primary_key=True),
        db.Column("id", db.UUIDType, nullable=False),
        db.Column("entry_id", db.Text(100), nullable=False),
        db.Column("user_id", db.Text, nullable=False),
        db.Column("timestamp", db.Integer, nullable=False),
        db.Column("body", db.NestedMutableJson, nullable=False),
        db.Column("version", db.Integer, nullable=False),
        db.Column("message", db.Text),
        db.Column("op", db.Enum(EntryOp), nullable=False),
        db.UniqueConstraint("id", "version", name="id_version_unique_constraint"),
        mysql_character_set="utf8mb4",
    )

    # db.mapper(
    #     Entry if not _use_aliased else db.aliased(Entry),
    #     table,
    #     properties={
    #         "_id": table.c.id,
    #         "_version": table.c.version,
    #         "_entry_id": table.c.entry_id,
    #         "_last_modified_by": table.c.user_id,
    #         "_last_modified": table.c.timestamp,
    #         "_body": table.c.body,
    #         "_message": table.c.message,
    #         "_op": table.c.op,
    #     },
    #     # non_primary=_non_primary,
    # )
    # if not _use_aliased:
    #     _use_aliased = True
    table.create(db.get_engine(db_uri))
    return table
