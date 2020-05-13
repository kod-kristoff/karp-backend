import pytest

from karp.domain.model.resource import ResourceCategory
from karp.domain.model.entry import EntryOp, create_entry
from karp.domain.model.entry_repository import EntryRepository

from karp.infrastructure.unit_of_work import unit_of_work
from karp.infrastructure.sql.legacy_entry_repository import (
    to_entry_op,
    to_legacy_entry_op,
    LegacyEntryOp,
    SqlLegacyEntryRepository,
)


def test_legacy_entry_op_to_entry_op():
    assert to_entry_op(LegacyEntryOp.ADDED) == EntryOp.ADDED
    assert to_entry_op(LegacyEntryOp.CHANGED) == EntryOp.UPDATED
    assert to_entry_op(LegacyEntryOp.REMOVED) == EntryOp.DELETED
    assert to_entry_op(LegacyEntryOp.IMPORTED) == EntryOp.ADDED


def test_str_legacy_entry_op_to_entry_op():
    assert to_entry_op("added") == EntryOp.ADDED
    assert to_entry_op(LegacyEntryOp.CHANGED) == EntryOp.UPDATED
    assert to_entry_op(LegacyEntryOp.REMOVED) == EntryOp.DELETED
    assert to_entry_op(LegacyEntryOp.IMPORTED) == EntryOp.ADDED


def test_entry_op_to_legacy_entry_op():
    assert to_legacy_entry_op(EntryOp.ADDED) == LegacyEntryOp.ADDED
    assert to_legacy_entry_op(EntryOp.UPDATED) == LegacyEntryOp.CHANGED
    assert to_legacy_entry_op(EntryOp.DELETED) == LegacyEntryOp.REMOVED


@pytest.fixture(name="entry_repo", scope="session")
def fixture_entry_repo():
    entry_repo = EntryRepository.create(
        "sql_legacy_v1",
        {
            "resource_id": "legacy_lexicon_entries",
            "db_uri": "sqlite:///",
            "table_name": "karpentry",
            "lexicon_id": "test_legacy_lexicon",
        },
    )
    assert entry_repo.type == "sql_legacy_v1"
    assert entry_repo.category == ResourceCategory.ENTRY_REPOSITORY
    assert isinstance(entry_repo, SqlLegacyEntryRepository)
    return entry_repo


def test_create_sql_legacy_entry_repository(entry_repo):

    assert entry_repo.db_uri == "sqlite:///"
    assert entry_repo.lexicon_id == "test_legacy_lexicon"
    with unit_of_work(using=entry_repo) as uw:
        assert uw.entry_ids() == []


def test_put_entry_to_legacy_entry_repo(entry_repo):
    with unit_of_work(using=entry_repo) as uw:
        entry = create_entry("a", {})
        uw.put(entry)
        uw.commit()

        assert uw.entry_ids() == ["a"]
