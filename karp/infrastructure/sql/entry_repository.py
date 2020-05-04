"""SQL repository for entries."""
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from karp.domain.model.entry import Entry, EntryOp, Repository as EntryRepository

from karp.infrastructure.sql import db
from karp.infrastructure.sql.sql_repository import SqlRepository


class SqlEntryRepository(EntryRepository, SqlRepository):
    def __init__(
        self,
        db_uri: str,
        history_table: db.Table,
        runtime_table: db.Table,
        # mapped_class: Any
    ):
        super().__init__(db_uri)
        self.history_table = history_table
        self.runtime_table = runtime_table
        # self.mapped_class = mapped_class

    def put(self, entry: Entry):
        self._check_has_session()
        history_id = self._insert_history(entry)
        # ins_stmt = db.insert(self.history_table)
        # ins_stmt = ins_stmt.values(self._entry_to_history_row(entry))
        # result = self._session.execute(ins_stmt)
        # history_id = result.lastrowid or result.returned_defaults["history_id"]

        ins_stmt = db.insert(self.runtime_table)
        ins_stmt = ins_stmt.values(self._entry_to_runtime_row(history_id, entry))
        result = self._session.execute(ins_stmt)
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

    def update(self, entry: Entry):
        self._check_has_session()
        history_id = self._insert_history(entry)

        updt_stmt = db.update(self.runtime_table)
        updt_stmt = updt_stmt.where(self.runtime_table.c.entry_id == entry.entry_id)
        updt_stmt = updt_stmt.values(self._entry_to_runtime_row(history_id, entry))

        result = self._session.execute(updt_stmt)

    def _insert_history(self, entry: Entry):
        self._check_has_session()
        ins_stmt = db.insert(self.history_table)
        ins_stmt = ins_stmt.values(self._entry_to_history_row(entry))
        result = self._session.execute(ins_stmt)
        history_id = result.lastrowid or result.returned_defaults["history_id"]
        return history_id

    def entry_ids(self) -> List[str]:
        self._check_has_session()
        query = self._session.query(self.runtime_table.c.entry_id)
        return [
            row.entry_id for row in query.all()
        ]

    def by_entry_id(self, entry_id: str) -> Optional[Entry]:
        self._check_has_session()
        query = self._session.query(*self.history_table.columns + self.runtime_table.columns)
        query = query.join(self.runtime_table, self.history_table.c.history_id == self.runtime_table.c.history_id)
        return self._history_row_to_entry(
            query.filter_by(entry_id=entry_id)
            .first()
        )
           # .order_by(self.mapped_class._version.desc())

    def by_id(self, id: str) -> Optional[Entry]:
        self._check_has_session()
        query = self._session.query(*self.history_table.columns + self.runtime_table.columns)
        return (
            query.filter_by(id=id).order_by(self.history_table.c.version.desc()).first()
        )

    def history_by_entry_id(self, entry_id: str) -> List[Entry]:
        self._check_has_session()
        query = self._session.query(*self.history_table.columns + self.runtime_table.columns)
        query = query.join(self.runtime_table, self.history_table.c.id == self.runtime_table.c.id)
        return query.filter_by(entry_id=entry_id).all()

    def _entry_to_history_row(
        self, entry: Entry
    ) -> Tuple[None, UUID, int, str, Dict, int, str, EntryOp, bool]:
        return (
            None,  # history_id
            entry.id,  # id
            # entry.entry_id,  # entry_id
            int(entry.last_modified),  # last_modified
            entry.last_modified_by,  # last_modified_by
            entry.body,  # body
            entry.version,  # version
            entry.message,  # message
            entry.op,  # op
            entry.discarded
        )

    def _history_row_to_entry(self, row) -> Entry:
        return Entry(
            entry_id=row.entry_id,
            body=row.body,
            entity_id=row.id,
            last_modified=row.last_modified,
            last_modified_by=row.last_modified_by,
            version=row.version,
            op=row.op,
            message=row.message,
            discarded=row.discarded,
        )

    def _entry_to_runtime_row(self, history_id: int, entry: Entry) -> Tuple[Optional[int], int, UUID]:
        return (entry.entry_id, history_id, entry.id)


def create_repository(db_uri: str, table_name: str) -> SqlEntryRepository:
    history_table = db.get_table(table_name) or create_history_entry_table(table_name, db_uri)

#     mapped_class = db.map_class_to_some_table(
#         Entry,
#         history_table,
#         f"Entry_{table_name}",
#         properties={
#             "_id": table.c.id,
#             "_version": table.c.version,
#             "_entry_id": table.c.entry_id,
#             "_last_modified_by": table.c.user_id,
#             "_last_modified": table.c.timestamp,
#             "_body": table.c.body,
#             "_message": table.c.message,
#             "_op": table.c.op,
#         },
#     )
    runtime_table_name = f"runtime_{table_name}"

    runtime_table = db.get_table(runtime_table_name) or create_entry_runtime_table(f"runtime_{table_name}", db_uri, history_table)
    return SqlEntryRepository(
        db_uri,
        history_table,
        runtime_table
    )


_use_aliased = False


def create_history_entry_table(table_name: str, db_uri: str) -> db.Table:
    global _use_aliased
    table = db.Table(
        table_name,
        db.metadata(db_uri),
        db.Column("history_id", db.Integer, primary_key=True),
        db.Column("id", db.UUIDType, nullable=False),
        # db.Column("entry_id", db.Text(100), nullable=False),
        db.Column("last_modified", db.Integer, nullable=False),
        db.Column("last_modified_by", db.Text, nullable=False),
        db.Column("body", db.NestedMutableJson, nullable=False),
        db.Column("version", db.Integer, nullable=False),
        db.Column("message", db.Text),
        db.Column("op", db.Enum(EntryOp), nullable=False),
        db.Column("discarded", db.Boolean, default=False),
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


def create_entry_runtime_table(
    table_name: str,
    db_uri: str,
    history_table: db.Table
) -> db.Table:
    table = db.Table(
        table_name,
        db.metadata(db_uri),
        db.Column("entry_id", db.Text(100), primary_key=True),
        db.Column("history_id", db.Integer, db.ForeignKey(history_table.c.history_id)),
        db.Column("id", db.UUIDType, db.ForeignKey(history_table.c.id)),
    )
    table.create(db.get_engine(db_uri))
    return table
