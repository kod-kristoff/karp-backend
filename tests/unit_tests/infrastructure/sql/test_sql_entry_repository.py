from karp.infrastructure.sql.entry_repository import SqlEntryRepository


def test_create_entry_repository():
    entry_repo = SqlEntryRepository("sqlite:///")
