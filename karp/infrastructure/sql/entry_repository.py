"""SQL repository for entries."""
from typing import List

from karp.domain.model.entry import Entry, Repository as EntryRepository
from karp.infrastructure.sql.sql_repository import SqlRepository


class SqlEntryRepository(EntryRepository, SqlRepository):
    def __init__(self, db_uri):
        super().__init__(db_uri)

    def put(self, entry: Entry):
        pass

    def entry_ids(self) -> List[str]:
        return []
