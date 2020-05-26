"""LexicalResource"""
import abc
import enum
from uuid import UUID
from typing import Dict, Any, Optional, List

from karp.domain import constraints
from karp.domain.errors import ConfigurationError, RepositoryStatusError
from karp.domain.model import event_handler
from karp.domain.model.entity import Entity, TimestampedVersionedEntity
from karp.domain.model.events import DomainEvent
from karp.utility import unique_id


class ResourceOp(enum.Enum):
    ADDED = "ADDED"
    UPDATED = "UPDATED"
    DELETED = "DELETED"


class ResourceCategory(enum.Enum):
    GENERAL_RESOURCE = "general_resource"
    LEXICAL_RESOURCE = "lexical_resource"
    ENTRY_REPOSITORY = "entry_repository"
    MORPHOLOGY = "morphology"


class Resource(TimestampedVersionedEntity):
    _registry = {c: {} for c in ResourceCategory}
    type = None
    category = None

    def __init_subclass__(
        cls, resource_category: ResourceCategory, resource_type: str, **kwargs
    ):
        super().__init_subclass__(**kwargs)
        if resource_type is None:
            raise RuntimeError("Unallowed resource_type: resource_type = None")
        if resource_category is None:
            raise RuntimeError("Unallowed resource_category: resource_category = None")
        if resource_type in cls._registry[resource_category]:
            raise RuntimeError(
                f"A Resource with type '{resource_type}' already exists in category '{resource_category}': {cls._registry[resource_type]!r}"
            )

        cls.type = resource_type
        cls.category = resource_category
        cls._registry[resource_category][resource_type] = cls

    @classmethod
    def create_resource(
        cls,
        resource_category: ResourceCategory,
        resource_type: str,
        resource_config: Dict,
    ):
        try:
            resource_cls = cls._registry[resource_category][resource_type]
        except KeyError:
            raise ConfigurationError(
                f"Can't create a Resource of type '{resource_type}' from category '{resource_category}'"
            )
        return resource_cls.from_dict(resource_config)

    @classmethod
    def get_resource_class(cls, category: ResourceCategory, resource_type: str):
        if category is None and resource_type is None:
            return Resource
        elif category is None:
            category = ResourceCategory.GENERAL_RESOURCE

        try:
            resource_cls = cls._registry[category][resource_type]
            if isinstance(resource_cls, str):
                resource_type = resource_cls
                resource_cls = cls._registry[category][resource_type]
        except KeyError:
            raise ConfigurationError(
                f"Can't find a class of type '{resource_type}' in category '{category}'."
            )

        return resource_cls

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
        resource_id: str,
        name: str,
        config: Dict[str, Any],
        message: str,
        op: ResourceOp,
        *args,
        is_published: bool = False,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._resource_id = resource_id
        self._name = name
        self.is_published = is_published
        self.config = config
        self._message = message
        self._op = op
        self._releases = []

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
    def resource_ids(self):
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

    @abc.abstractmethod
    def get_all_resources(self) -> List[Resource]:
        raise NotImplementedError()
