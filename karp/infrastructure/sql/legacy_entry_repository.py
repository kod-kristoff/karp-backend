from typing import Dict

from karp.domain.models.entry import EntryRepository


class SqlLegacyEntryRepository(EntryRepository, repository_type="sql_legacy_v1"):
    @classmethod
    def from_dict(cls, settings: Dict):
        pass
