"""Entity"""
from karp.domain.common import _now, _unknown_user
from karp.domain.errors import ConsistencyError, DiscardedEntityError
from karp.domain.model.events import DomainEvent

from karp.utility.time import monotonic_utc_now


class Entity:
    class Discarded(DomainEvent):
        def mutate(self, obj):
            obj._discarded = True

    def __init__(self, entity_id):
        self._id = entity_id
        self._discarded = False

    @property
    def id(self):
        """A unique identifier for the entity."""
        return self._id

    @property
    def discarded(self) -> bool:
        """True if this entity is marked as deleted, otherwise False.
        """
        return self._discarded

    def _check_not_discarded(self):
        if self._discarded:
            raise DiscardedEntityError(f"Attempt to use {self!r}")

    def _validate_event_applicability(self, event):
        if event.entity_id != self.id:
            raise ConsistencyError(
                f"Event entity id mismatch: {event.entity_id} != {self.id}"
            )


class VersionedEntity(Entity):
    class Discarded(Entity.Discarded):
        def mutate(self, obj):
            obj._discarded = True
            obj._increment_version()

    def __init__(self, entity_id, version: int):
        super().__init__(entity_id)
        self._version = version

    @property
    def version(self) -> int:
        """An integer version for the entity."""
        return self._version

    def _increment_version(self):
        self._version += 1

    def _validate_event_applicability(self, event):
        if event.entity_id != self.id:
            raise ConsistencyError(
                f"Event entity id mismatch: {event.entity_id} != {self.id}"
            )
        if event.entity_version != self.version:
            raise ConsistencyError(
                f"Event entity version mismatch: {event.entity_version} != {self.version}"
            )


class TimestampedVersionedEntity(VersionedEntity):
    class Discarded(VersionedEntity.Discarded):
        def mutate(self, obj):
            super().mutate(obj)
            obj._last_modified = self.timestamp
            obj._last_modified_by = self.user

    def __init__(
        self, entity_id, version: int, created=_now, created_by=_unknown_user,
    ) -> None:
        super().__init__(entity_id, version)
        self._last_modified = monotonic_utc_now() if created is _now else created
        self._last_modified_by = (
            _unknown_user if created_by is _unknown_user else created_by
        )

    @property
    def last_modified(self):
        """The time this entity was last modified."""
        return self._last_modified

    @last_modified.setter
    def last_modified(self, timestamp):
        self._check_not_discarded()
        self._last_modified = timestamp

    @property
    def last_modified_by(self):
        """The time this entity was last modified."""
        return self._last_modified_by

    @last_modified_by.setter
    def last_modified_by(self, user):
        self._check_not_discarded()
        self._last_modified_by = user

    def stamp(self, user, *, timestamp=_now, increment_version=True):
        self._check_not_discarded()
        self._last_modified_by = user
        self._last_modified = monotonic_utc_now() if timestamp is _now else timestamp
        if increment_version:
            self._increment_version()
