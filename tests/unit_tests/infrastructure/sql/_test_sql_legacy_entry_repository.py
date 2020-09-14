from karp.domain.models.entry import (
    create_entry,
    EntryRepository,
)

from karp.infrastructure.sql.legacy_entry_repository import SqlLegacyEntryRepository


def test_create_sql_legacy_entry_repository():
    entry_repo = EntryRepository.create(
        "sql_legacy_v1",
        {
            "db_uri": "sqlite:///",
            "table_name": "karpentry",
            "lexicon_id": "test_legacy_lexicon",
        },
    )

    assert entry_repo.type == "sql_legacy_v1"
    assert isinstance(entry_repo, SqlLegacyEntryRepository)
