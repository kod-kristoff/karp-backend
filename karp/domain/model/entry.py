"""Model for a lexical entry."""
import abc
import enum
from typing import Dict, Optional, List

from karp.domain import constraints
from karp.domain.common import _now, _unknown_user
from karp.domain.model import event_handler
from karp.domain.model.entity import TimestampedVersionedEntity

from karp.utility import unique_id


class EntryOp(enum.Enum):
    ADDED = "ADDED"
    DELETED = "DELETED"
    UPDATED = "UPDATED"


class Entry(TimestampedVersionedEntity):
    class Discarded(TimestampedVersionedEntity.Discarded):
        def mutate(self, entry):
            super().mutate(entry)
            entry._op = EntryOp.DELETED
            entry._message = "Entry deleted." if self.message is None else self.message

    def __init__(
        self,
        entry_id: str,
        body: Dict,
        entity_id: unique_id.UniqueId,
        last_modified: Optional[float] = _now,
        last_modified_by: str = _unknown_user,
        op: EntryOp = EntryOp.ADDED,
        message: str = None,
        discarded: bool = False,
        version: int = 0
    ):
        super().__init__(
            entity_id=entity_id,
            version=version,
            last_modified=last_modified,
            last_modified_by=last_modified_by,
            discarded=discarded,
        )
        self._entry_id = entry_id
        self._body = body
        self._op = op
        self._message = "Entry added." if message is None else message

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

    def discard(self, *, user: str, message: str = None):
        event = Entry.Discarded(
            entity_id=self.id, entity_version=self.version, user=user, message=message
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


# === Factories ===
def create_entry(entry_id: str, body: Dict) -> Entry:
    entry = Entry(entry_id=entry_id, body=body, entity_id=unique_id.make_unique_id(), version=0)
    return entry


# === Repository ===
class Repository(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def put(self, entry: Entry):
        raise NotImplementedError()

    @abc.abstractmethod
    def entry_ids(self) -> List[str]:
        raise NotImplementedError()

    @abc.abstractmethod
    def by_entry_id(self, entry_id: str) -> Optional[Entry]:
        raise NotImplementedError()
