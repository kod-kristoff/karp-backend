"""LexicalResource"""
import abc
import enum
from uuid import UUID
from typing import Callable, Dict, Any, Optional, List, Union

from karp.domain import constraints, events  # , repository
from karp.domain.errors import ConfigurationError, RepositoryStatusError
from karp.domain.models import event_handler
from karp.domain.models.entity import Entity, TimestampedVersionedEntity
from karp.domain.models.entry import Entry, EntryRepository, create_entry
from karp.domain.models.events import DomainEvent
from karp.domain.models.auth_service import PermissionLevel

from karp.utility import unique_id
from karp.utility import json_schema
from karp.utility.container import create_field_getter


# pylint: disable=unsubscriptable-object


class ResourceOp(enum.Enum):
    ADDED = "ADDED"
    UPDATED = "UPDATED"
    DELETED = "DELETED"


class Resource(TimestampedVersionedEntity):
    _registry = {}

    def __init_subclass__(cls, resource_type: str, **kwargs):
        super().__init_subclass__(**kwargs)
        if resource_type is None:
            raise RuntimeError("Unallowed resource_type: resource_type = None")
        if resource_type in cls._registry:
            raise RuntimeError(
                f"A Resource with type '{resource_type}' already exists: {cls._registry[resource_type]!r}"
            )

        cls.type = resource_type
        cls._registry[resource_type] = cls

    @classmethod
    def create_resource(cls, resource_type: str, resource_config: Dict):
        try:
            resource_cls = cls._registry[resource_type]
        except KeyError:
            raise ConfigurationError(
                f"Can't create a Resource of type '{resource_type}"
            )
        return resource_cls.from_dict(resource_config)

    @classmethod
    def from_dict(cls, config: Dict, **kwargs):
        resource_id = config.pop("resource_id")
        resource_name = config.pop("resource_name")
        #     if "entry_repository_type" not in config:
        #         config["entry_repository_type"] = EntryRepository.get_default_repository_type()
        #     entry_repository_settings = config.get(
        #         "entry_repository_settings")
        #     if entry_repository_settings is None:
        #         entry_repository_settings = EntryRepository.create_repository_settings(
        #             config["entry_repository_type"],
        #             resource_id
        #         )
        #
        #     entry_repository = EntryRepository.create(
        #         config["entry_repository_type"],
        #         entry_repository_settings
        #     )

        resource = cls(
            resource_id,
            resource_name,
            config,
            message="Resource added.",
            op=ResourceOp.ADDED,
            entity_id=unique_id.make_unique_id(),
            version=1,
            **kwargs,
        )
        return resource

    class Discarded(TimestampedVersionedEntity.Discarded):
        def mutate(self, obj):
            super().mutate(obj)

    class Stamped(TimestampedVersionedEntity.Stamped):
        def mutate(self, obj):
            super().mutate(obj)
            obj._message = self.message
            obj._op = ResourceOp.UPDATED

    class NewReleaseAdded(DomainEvent):
        def mutate(self, obj):
            obj._validate_event_applicability(self)
            release = Release(
                entity_id=self.release_id,
                name=self.release_name,
                publication_date=self.timestamp,
                description=self.release_description,
                aggregate_root=obj,
            )
            obj._releases.append(release)
            obj._last_modified = self.timestamp
            obj._last_modified_by = self.user
            obj._message = f"Release '{self.release_name}' created."
            obj._increment_version()

    def __init__(
        self,
        *,
        resource_id: unique_id.UniqueId,
        machine_name: str,
        name: str,
        config: Dict[str, Any],
        message: str,
        op: ResourceOp = ResourceOp.ADDED,
        is_published: bool = False,
        entry_repository: EntryRepository = None,
        entries=None,  # type: Optional[repository.EntryRepository]
        version: int = 1,
        **kwargs,
    ):
        super().__init__(entity_id=resource_id, version=version, **kwargs)
        self._resource_id = resource_id
        self.machine_name = machine_name
        self._name = name
        self.is_published = is_published
        self.config = config
        self._message = message
        self._op = op
        self._releases = []
        self._entry_repository = entry_repository
        self._entry_json_schema = None
        self.entries = entries
        self.events: List[events.Event] = []
        print(f"self.entries = {entries}")
        self.entries = entries
        self.events.append(events.ResourceCreated(resource_id))

    @property
    def resource_id(self):
        return self._resource_id

    @property
    def name(self):
        return self._name

    @property
    def message(self):
        return self._message

    @property
    def releases(self):
        """Releases for this resource."""
        return self._releases

    @property
    def op(self):
        return self._op

    @property
    def entry_repository(self) -> EntryRepository:
        if self._entry_repository is None:
            self._entry_repository = EntryRepository.create(
                None, {"table_name": self._resource_id, "config": self.config}
            )
        return self._entry_repository

    def stamp(self, *, user: str, message: str = None, increment_version: bool = True):
        self._check_not_discarded()
        event = Resource.Stamped(
            entity_id=self.id,
            entity_version=self.version,
            entity_last_modified=self.last_modified,
            user=user,
            message=message,
            increment_version=increment_version,
        )
        event.mutate(self)
        event_handler.publish(event)

    def add_new_release(self, *, name: str, user: str, description: str):
        self._check_not_discarded()
        event = Resource.NewReleaseAdded(
            entity_id=self.id,
            entity_version=self.version,
            entity_last_modified=self.last_modified,
            release_id=unique_id.make_unique_id(),
            release_name=constraints.length_gt_zero("name", name),
            user=user,
            release_description=description,
        )
        event.mutate(self)
        event_handler.publish(event)

        return self.release_with_name(name)

    def release_with_name(self, name: str):
        self._check_not_discarded()
        pass

    def discard(self, *, user: str, message: str):
        self._check_not_discarded()
        event = Resource.Discarded(
            entity_id=self.id,
            entity_version=self.version,
            entity_last_modified=self.last_modified,
            user=user,
            message=message,
        )

        event.mutate(self)
        event_handler.publish(event)

    @property
    def entry_json_schema(self) -> Dict:
        if self._entry_json_schema is None:
            self._entry_json_schema = json_schema.create_entry_json_schema(
                self.config["fields"]
            )
        return self._entry_json_schema

    # @property
    def id_getter(self) -> Callable[[Dict], str]:
        return create_field_getter(self.config["id"], str)

    def create_entry_from_dict(
        self, entry_raw: Dict, *, user: str, message: Optional[str] = None
    ) -> Entry:
        self._check_not_discarded()
        id_getter = self.id_getter()
        return create_entry(
            id_getter(entry_raw),
            entry_raw,
            last_modified_by=user,
            message=message,
        )

    def is_protected(self, level: PermissionLevel):
        """
        Level can be READ, WRITE or ADMIN
        """
        protection = self.config.get("protected", {})
        return level == "WRITE" or level == "ADMIN" or protection.get("read")


# ===== Entities =====
class Release(Entity):
    def __init__(self, name: str, publication_date: float, description: str, **kwargs):
        super().__init__(**kwargs)
        self._name = name
        self._publication_date = publication_date
        self._description = description

    @property
    def name(self) -> str:
        """The name of this release."""
        return self._name

    @property
    def publication_date(self) -> float:
        """The publication of this release."""
        return self._publication_date

    @property
    def description(self) -> str:
        """The description of this release."""
        return self._description


# ===== Factories =====


def create_resource(config: Dict) -> Resource:
    resource_id = config.pop("resource_id")
    resource_name = config.pop("resource_name")
    #     if "entry_repository_type" not in config:
    #         config["entry_repository_type"] = EntryRepository.get_default_repository_type()
    #     entry_repository_settings = config.get(
    #         "entry_repository_settings")
    #     if entry_repository_settings is None:
    #         entry_repository_settings = EntryRepository.create_repository_settings(
    #             config["entry_repository_type"],
    #             resource_id
    #         )
    #
    #     entry_repository = EntryRepository.create(
    #         config["entry_repository_type"],
    #         entry_repository_settings
    #     )

    resource = Resource(
        resource_id,
        resource_name,
        config,
        message="Resource added.",
        op=ResourceOp.ADDED,
        entity_id=unique_id.make_unique_id(),
        version=1,
    )
    return resource


# ===== Repository =====


class ResourceRepository(metaclass=abc.ABCMeta):
    def check_status(self):
        raise RepositoryStatusError()

    @abc.abstractmethod
    def put(self, resource: Resource):
        raise NotImplementedError()

    @abc.abstractmethod
    def resource_ids(self) -> List[Resource]:
        raise NotImplementedError()

    @abc.abstractmethod
    def by_id(
        self, id: Union[UUID, str], *, version: Optional[int] = None
    ) -> Optional[Resource]:
        raise NotImplementedError()

    @abc.abstractmethod
    def by_resource_id(
        self, resource_id: str, *, version: Optional[int] = None
    ) -> Optional[Resource]:
        raise NotImplementedError()

    @abc.abstractmethod
    def resources_with_id(self, resource_id: str):
        raise NotImplementedError()

    @abc.abstractmethod
    def resource_with_id_and_version(self, resource_id: str, version: int):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_active_resource(self, resource_id: str) -> Optional[Resource]:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_published_resources(self) -> List[Resource]:
        raise NotImplementedError()
