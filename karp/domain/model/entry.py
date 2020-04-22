"""Model for a lexical entry."""
import abc
from typing import Dict, Optional

from karp.domain import common
from karp.domain import constraints
from karp.domain.model import event_handler
from karp.domain.model.entity import TimestampedVersionedEntity


class Entry(TimestampedVersionedEntity):
    class Discarded(TimestampedVersionedEntity.Discarded):
        pass

    def __init__(
        self,
        entry_id: str,
        body: Dict,
        entity_id: Optional[int] = None,
        created: Optional[float] = common._now,
        created_by: str = common._unknown_user,
    ):
        super().__init__(
            entity_id=entity_id, version=0, created=created, created_by=created_by
        )
        self._entry_id = entry_id
        self._body = body

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

    def discard(self, *, user: str):
        event = Entry.Discarded(
            entity_id=self.id,
            entity_version=self.version,
            user=user
        )
        event.mutate(self)
        event_handler.publish(event)


class Repository:
    @abc.abstractmethod
    def put(self, entry: Entry):
        raise NotImplementedError()

    @abc.abstractmethod
    def entry_ids(self) -> List[str]:
        raise NotImplementedError()
