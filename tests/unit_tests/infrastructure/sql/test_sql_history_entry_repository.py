import pytest

from karp.domain.model.entry import Entry

from karp.infrastructure.unit_of_work import unit_of_work
from karp.infrastructure.sql.entry_repository import SqlEntryRepository


@pytest.fixture(name="entry_repo", scope="session")
def fixture_entry_repo():
    entry_repo = SqlEntryRepository("sqlite:///")
    return entry_repo


def test_create_entry_repository():
    entry_repo = SqlEntryRepository("sqlite:///")
    assert entry_repo.db_uri == "sqlite:///"
    assert entry_repo.entry_ids() == []


def test_put_entry(entry_repo):
    with unit_of_work(using=entry_repo) as uw:
        uw.put(Entry("a", {}))
        uw.commit()

        assert uw.entry_ids() == ["a"]
