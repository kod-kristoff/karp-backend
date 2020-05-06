"""LexicalResource"""
import abc
import enum
from typing import Dict, Any, Optional

from karp.domain import constraints
from karp.domain.errors import RepositoryStatusError
from karp.domain.model import event_handler
from karp.domain.model.entity import Entity, TimestampedVersionedEntity
from karp.domain.model.events import DomainEvent
from karp.utility import unique_id


class ResourceOp(enum.Enum):
    ADDED = "ADDED"
    UPDATED = "UPDATED"
    DELETED = "DELETED"


class Resource(TimestampedVersionedEntity):
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
        is_active: bool = False,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._resource_id = resource_id
        self._name = name
        self.is_active = is_active
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
