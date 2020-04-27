"""SQL repository for entries."""
from typing import List

from karp.domain.model.entry import Entry, Repository as EntryRepository

from karp.infrastructure.sql import db
from karp.infrastructure.sql.sql_repository import SqlRepository


class SqlEntryRepository(EntryRepository, SqlRepository):
    def __init__(self, db_uri: str, table: db.Table):
        super().__init__(db_uri)
        self._table = table

    def put(self, entry: Entry):
        pass

    def entry_ids(self) -> List[str]:
        return []


def create_repository(
    db_uri: str,
    table_name: str
) -> SqlEntryRepository:
    table = db.get_table(table_name)
    if not table:
        table = create_entry_table(table_name, db_uri)
    return SqlEntryRepository(db_uri, table)


def create_entry_table(
    table_name: str,
    db_uri: str
) -> db.Table:
    table = db.Table(
        table_name,
        db.metadata(db_uri),
        db.Column("id", db.Integer, primary_key=True),
        db.Column("entry_id", db.Unicode(100, mysql_collation="utf8_bin"), nullable=False),
        db.Column("user_id", db.Text, nullable=False),
        db.Column("timestamp", db.Integer, nullable=False),
        db.Column("body")
    )
    return table
