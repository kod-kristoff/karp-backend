"""Entity"""
from karp.domain.errors import ConsistencyError, DeletedEntityError


class Entity:
    def __init__(self, entity_id):
        self._id = entity_id
        self._deleted = False

    @property
    def id(self):
        """A unique identifier for the entity."""
        return self._id

    @property
    def is_deleted(self) -> bool:
        """True if this entity is marked as deleted, otherwise False.
        """
        return self._deleted

    def _check_not_deleted(self):
        if self._deleted:
            raise DeletedEntityError(f"Attempt to use {self!r}")

    def _validate_event_applicability(self, event):
        if event.entity_id != self.id:
            raise ConsistencyError(
                f"Event entity id mismatch: {event.entity_id} != {self.id}"
            )


class VersionedEntity(Entity):
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
