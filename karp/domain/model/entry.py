"""Model for a lexical entry."""
import abc
import enum
from typing import Dict, Optional, List

from karp.domain import constraints
from karp.domain.common import _now, _unknown_user
from karp.domain.model import event_handler
from karp.domain.model.entity import TimestampedVersionedEntity


class EntryOp(enum.Enum):
    ADDED = "ADDED"
    DELETED = "DELETED"
    UPDATED = "UPDATED"


class Entry(TimestampedVersionedEntity):
    class Discarded(TimestampedVersionedEntity.Discarded):
        def mutate(self, entry):
            super().mutate(entry)
            entry._op = EntryOp.DELETED
            entry._message = "Entry deleted."

    def __init__(
        self,
        entry_id: str,
        body: Dict,
        entity_id: Optional[int] = None,
        created: Optional[float] = _now,
        created_by: str = _unknown_user,
    ):
        super().__init__(
            entity_id=entity_id, version=0, created=created, created_by=created_by
        )
        self._entry_id = entry_id
        self._body = body
        self._op = EntryOp.ADDED
        self._message = "Entry added."

    @property
    def entry_id(self):
        """The entry_id of this entry."""
        return self._entry_id

    @entry_id.setter
    def entry_id(self, entry_id: str):
        self._check_not_discarded()
        self._entry_id = constraints.length_gt_zero("entry_id", entry_id)

    @property
    def body(self):
        """The body of the entry."""
        return self._body

    @body.setter
    def body(self, body: Dict):
        self._check_not_discarded()
        self._body = body

    @property
    def op(self):
        """The latest operation of this entry."""
        return self._op

    @property
    def message(self):
        """The message for the latest operation of this entry."""
        return self._message

    def discard(self, *, user: str):
        event = Entry.Discarded(
            entity_id=self.id,
            entity_version=self.version,
            user=user
        )
        event.mutate(self)
        event_handler.publish(event)

    def stamp(
        self,
        user: str,
        *,
        message: str = None,
        timestamp: float = _now,
        increment_version: bool = True
    ):
        super().stamp(user, timestamp=timestamp, increment_version=increment_version)
        self._message = message
        self._op = EntryOp.UPDATED


class Repository(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def put(self, entry: Entry):
        raise NotImplementedError()

    @abc.abstractmethod
    def entry_ids(self) -> List[str]:
        raise NotImplementedError()
