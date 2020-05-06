"""Model for a lexical entry."""
import abc
import enum
from functools import singledispatch
from typing import Dict, Optional, List
from uuid import UUID

from karp.domain import constraints
from karp.domain.common import _now, _unknown_user
from karp.domain.model import event_handler
from karp.domain.model.entity import TimestampedEntity

from karp.utility import unique_id


class EntryOp(enum.Enum):
    ADDED = "ADDED"
    DELETED = "DELETED"
    UPDATED = "UPDATED"


class EntryStatus(enum.Enum):
    IN_PROGRESS = "IN-PROGRESS"
    IN_REVIEW = "IN_REVIEW"
    OK = "OK"


class Entry(TimestampedEntity):
    class Discarded(TimestampedEntity.Discarded):
        def mutate(self, entry):
            super().mutate(entry)
            entry._op = EntryOp.DELETED
            entry._message = "Entry deleted." if self.message is None else self.message

    def __init__(
        self,
        entry_id: str,
        body: Dict,
        message: str,
        status: EntryStatus,  # IN-PROGRESS, IN-REVIEW, OK, PUBLISHED
        op: EntryOp,
        *pos,
        **kwargs,
        # version: int = 0
    ):
        super().__init__(*pos, **kwargs)
        self._entry_id = entry_id
        self._body = body
        self._op = op
        self._message = "Entry added." if message is None else message
        self._status = status

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
    def status(self):
        """The workflow status of this entry."""
        return self._status

    @status.setter
    def status(self, status: EntryStatus):
        """The workflow status of this entry."""
        self._check_not_discarded()
        self._status = status

    @property
    def message(self):
        """The message for the latest operation of this entry."""
        return self._message

    def discard(self, *, user: str, message: str = None):
        event = Entry.Discarded(
            entity_id=self.id,
            entity_last_modified=self.last_modified,
            user=user,
            message=message,
        )
        event.mutate(self)
        event_handler.publish(event)

    def stamp(
        self, user: str, *, message: str = None, timestamp: float = _now,
    ):
        super().stamp(user, timestamp=timestamp)
        self._message = message
        self._op = EntryOp.UPDATED


# === Factories ===
def create_entry(entry_id: str, body: Dict, message: Optional[str] = None) -> Entry:
    entry = Entry(
        entry_id=entry_id,
        body=body,
        message="Entry added." if not message else message,
        status=EntryStatus.IN_PROGRESS,
        op=EntryOp.ADDED,
        entity_id=unique_id.make_unique_id(),
    )
    return entry


# === Repository ===
class EntryRepository(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def put(self, entry: Entry):
        raise NotImplementedError()

    @abc.abstractmethod
    def entry_ids(self) -> List[str]:
        raise NotImplementedError()

    @abc.abstractmethod
    def by_entry_id(self, entry_id: str) -> Optional[Entry]:
        raise NotImplementedError()


class EntryRepositorySettings:
    """Settings for an EntryRepository."""

    pass


@singledispatch
def create_entry_repository(settings: EntryRepositorySettings) -> EntryRepository:
    raise RuntimeError(f"Don't know how to handle {settings!r}")
