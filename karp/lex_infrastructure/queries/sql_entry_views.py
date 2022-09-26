import typing

from sqlalchemy.engine import Connection

from karp.foundation.value_objects import UniqueId
from karp.lex import EntryViews, EntryDto

from karp.lex_infrastructure.sql import sql_models

class SqlEntryViews(EntryViews):
    def __init__(self, connection: Connection) -> None:
        self._conn = connection

    def create_resource(self, resource_id: str, resource_config: dict):
        runtime_model = sql_models.get_or_create_entry_runtime_model(
            event.resource_id, None, event.config
        )
        
    def all_entries(self, resource_id: str) -> typing.Iterable[EntryDto]:
        return super().all_entries(resource_id)

    def get_by_entry_id(self, resource_id: str, entry_id: str) -> EntryDto:
        return super().get_by_entry_id(resource_id, entry_id)

    def get_by_entry_id_optional(
        self, resource_id: str, entry_id: str
    ) -> typing.Optional[EntryDto]:
        return super().get_by_entry_id_optional(resource_id, entry_id)

    def get_by_id(self, resource_id: str, id: UniqueId) -> EntryDto:
        raise NotImplementedError("")

    def get_by_id_optional(
        self, resource_id: str, id: UniqueId
    ) -> typing.Optional[EntryDto]:
        raise NotImplementedError("")

    def get_by_referenceable(
        self, resource_id: str, filters
    ) -> typing.Iterable[EntryDto]:
        return super().get_by_referenceable(resource_id, filters)

    def get_total(self):
        raise NotImplementedError("")
