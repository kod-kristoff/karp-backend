"""Model for a lexical entry."""
import abc
import enum
from functools import singledispatch
import logging
from typing import Dict, Optional, List
from uuid import UUID
from abc import abstractclassmethod

from karp.domain import constraints
from karp.domain.errors import ConfigurationError
from karp.domain.common import _now, _unknown_user
from karp.domain.model import event_handler
from karp.domain.model.entry import Entry
from karp.domain.model.resource import Resource, ResourceCategory

from karp.utility import unique_id


_logger = logging.getLogger("karp")


# === Repository ===
class EntryRepository(
    Resource,
    metaclass=abc.ABCMeta,
    resource_category=ResourceCategory.ENTRY_REPOSITORY,
    resource_type="entry_repository",
):
    def __init_subclass__(
        cls, repository_type: str, is_default: bool = False, **kwargs
    ) -> None:
        super().__init_subclass__(
            resource_category=ResourceCategory.ENTRY_REPOSITORY,
            resource_type=repository_type,
            **kwargs,
        )
        print(
            f"EntryRepository.__init_subclass__ called with repository_type={repository_type} and is_default={is_default}"
        )
        if repository_type is None:
            raise RuntimeError("Unallowed repository_type: repository_type = None")
        # if repository_type in cls._registry[ResourceCategory.ENTRY_REPOSITORY]:
        #     raise RuntimeError(
        #         f"An EntryRepository with type '{repository_type}' already exists: {cls._registry[ResourceCategory.ENTRY_REPOSITORY][repository_type]!r}"
        #     )

        # if is_default and None in cls._registry:
        #     raise RuntimeError(f"A default EntryRepository is already set. Default type is {cls._registry[None]!r}")
        # cls.type = repository_type
        # cls._registry[repository_type] = cls
        if is_default:
            if None in cls._registry[ResourceCategory.ENTRY_REPOSITORY]:
                _logger.warn(
                    "Setting default EntryRepository type to '%s'", repository_type
                )
            cls._registry[ResourceCategory.ENTRY_REPOSITORY][None] = repository_type
        if None not in cls._registry[ResourceCategory.ENTRY_REPOSITORY]:
            cls._registry[ResourceCategory.ENTRY_REPOSITORY][None] = repository_type

    @classmethod
    def get_default_repository_type(cls) -> Optional[str]:
        return cls._registry[ResourceCategory.ENTRY_REPOSITORY][None]

    @classmethod
    def create(cls, repository_type: Optional[str], settings: Dict):
        print(f"_registry={cls._registry}")
        if repository_type is None:
            repository_type = cls._registry[ResourceCategory.ENTRY_REPOSITORY][None]
        try:
            repository_cls = cls._registry[ResourceCategory.ENTRY_REPOSITORY][
                repository_type
            ]
        except KeyError:
            raise ConfigurationError(
                f"Can't create an EntryRepository with type '{repository_type}'"
            )
        return repository_cls.from_dict(settings)

    @classmethod
    def create_repository_settings(cls, repository_type: str, resource_id: str) -> Dict:
        repository_cls = cls._registry[ResourceCategory.ENTRY_REPOSITORY][
            repository_type
        ]
        return repository_cls._create_repository_settings(resource_id)

    @classmethod
    @abc.abstractmethod
    def from_dict(cls, settings: Dict):
        raise NotImplementedError()

    @classmethod
    @abc.abstractmethod
    def _create_repository_settings(cls, resource_id: str):
        raise NotImplementedError()

    @abc.abstractmethod
    def put(self, entry: Entry):
        raise NotImplementedError()

    @abc.abstractmethod
    def entry_ids(self) -> List[str]:
        raise NotImplementedError()

    @abc.abstractmethod
    def by_entry_id(self, entry_id: str) -> Optional[Entry]:
        raise NotImplementedError()


# class EntryRepositorySettings:
#     """Settings for an EntryRepository."""

#     pass


# @singledispatch
# def create_entry_repository(settings: EntryRepositorySettings) -> EntryRepository:
#     raise RuntimeError(f"Don't know how to handle {settings!r}")
