import abc
import logging
from typing import List, Generic, TypeVar

import injector


logger = logging.getLogger(__name__)


T = TypeVar("T")


class Event:
    pass


class EventMixin:
    def __init__(self) -> None:
        self._pending_domain_events: List[Event] = []

    def _record_event(self, event: Event) -> None:
        self._pending_domain_events.append(event)

    @property
    def domain_events(self) -> List[Event]:
        return self._pending_domain_events[:]

    def clear_events(self) -> None:
        self._pending_domain_events.clear()


class EventHandler(Generic[T]):
    """Simple generic used to associate handlers with events using DI.

    e.g EventHandler[ResourceCreated].
    """

    pass


class EventBus(abc.ABC):
    @abc.abstractmethod
    def post(self, event: Event) -> None:
        raise NotImplementedError


class InjectorEventBus(EventBus):
    def __init__(self, container: injector.Injector) -> None:
        self._container = container

    def post(self, event: Event) -> None:
        try:
            evt_handlers = self._container.get(
                List[EventHandler[type(event)]]  # type: ignore
            )
        except injector.UnsatisfiedRequirement:
            logger.info('No event handler for event %s', event)
        else:
            for evt_handler in evt_handlers:
                logger.debug(
                    'handling event %s with handler %s',
                    event, evt_handler
                )
                try:
                    evt_handler(event)
                except Exception:
                    logger.exception('Exception handling event %s', event)
