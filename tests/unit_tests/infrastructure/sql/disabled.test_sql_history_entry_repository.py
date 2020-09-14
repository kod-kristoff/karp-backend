import pytest

from karp.domain.models.history_entry import HistoryEntry

from karp.infrastructure.unit_of_work import unit_of_work
from karp.infrastructure.sql.history_entry_repository import SqlHistoryEntryRepository


@pytest.fixture(name="history_entry_repo", scope="session")
def fixture_history_entry_repo():
    history_entry_repo = SqlHistoryEntryRepository("sqlite:///")
    return history_entry_repo


def test_create_history_entry_repository():
    history_entry_repo = SqlHistoryEntryRepository("sqlite:///")
    assert history_entry_repo.db_uri == "sqlite:///"
    assert history_entry_repo.entry_ids() == []


def test_put_entry(history_entry_repo):
    with unit_of_work(using=history_entry_repo) as uw:
        uw.put(HistoryEntry("a", {}))
        uw.commit()

        assert uw.entry_ids() == ["a"]
