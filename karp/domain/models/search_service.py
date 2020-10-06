from typing import Optional, Callable, TypeVar, List, Dict, Tuple
import logging

from karp.domain.errors import ConfigurationError

from karp.domain.models.query import Query
from karp.domain.models.entry import Entry


logger = logging.getLogger("karp")


class SearchService:
    _registry = {}

    def __init_subclass__(
        cls, search_service_type: str, is_default: bool = False, **kwargs
    ) -> None:
        super().__init_subclass__(**kwargs)
        if search_service_type is None:
            raise RuntimeError(
                "Unallowed search_service_type: search_service_type = None"
            )
        if search_service_type in cls._registry:
            raise RuntimeError(
                f"An SearchService with type '{search_service_type}' already exists: {cls._registry[search_service_type]!r}"
            )
        search_service_type = search_service_type.lower()
        cls._registry[search_service_type] = cls
        if is_default or None not in cls._registry:
            logger.info(
                "Setting default SearchService type to '%s'", search_service_type
            )
            cls._registry[None] = search_service_type

    @classmethod
    def create(cls, search_service_type: Optional[str]):
        if search_service_type is None:
            search_service_type = cls._registry[None]
        else:
            search_service_type = search_service_type.lower()

        try:
            search_service_cls = cls._registry[search_service_type]
        except KeyError:
            raise ConfigurationError(
                f"Can't create a SearchService of type '{search_service_type}'"
            )
        return search_service_cls()

    def create_index(self, resource_id: str, config: Dict) -> str:
        raise NotImplementedError()

    def publish_index(self, alias_name: str, index_name: str):
        raise NotImplementedError()

    def add_entries(self, resource_id: str, entries: List[Entry]):
        raise NotImplementedError()

    def delete_entry(self, resource_id: str, entry_id: str):
        raise NotImplementedError()

    def create_empty_object(self):
        raise NotImplementedError()

    def assign_field(self, _index_entry, field_name: str, part):
        raise NotImplementedError()

    def create_empty_list(self):
        raise NotImplementedError()

    def add_to_list_field(self, elems: List, elem):
        raise NotImplementedError()

    def build_query(self, args, resource_str: str) -> Query:
        query = Query()
        query.parse_arguments(args, resource_str)
        return query

    def search_with_query(self, query: Query):
        raise NotImplementedError()

    def search_ids(self, args, resource_id: str, entry_ids: str):
        raise NotImplementedError()

    def statistics(self, resource_id: str, field: str):
        raise NotImplementedError()
