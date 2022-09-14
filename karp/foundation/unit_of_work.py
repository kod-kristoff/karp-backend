import abc
from collections.abc import Iterable
import logging
import typing

from karp.foundation.events import Event, EventBus


RepositoryType = typing.TypeVar("RepositoryType")


logger = logging.getLogger(__name__)


class UnitOfWork(typing.Generic[RepositoryType], abc.ABC):
    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus
        self._pending_events: list[Event] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.rollback()
        self.close()

    def commit(self):
        logger.debug("called commit")
        self._commit()
        for event in self._pending_events:
            logger.debug("posting events")
            self.event_bus.post(event)
        self._pending_events.clear()

    # def collect_new_events(self) -> typing.Iterable:
    #     for entity in self.repo.seen:
    #         # yield from entity.domain_events
    #         yield from entity.collect_new_events()
    #         entity.clear_events()
    def record_events(self, events: Iterable[Event]) -> None:
        self._pending_events.extend(events)

    @abc.abstractmethod
    def _commit(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def rollback(self):
        pass

    @property
    @abc.abstractmethod
    def repo(self) -> RepositoryType:
        pass

    @abc.abstractmethod
    def _close(self):
        pass

    def close(self):
        self._close()
