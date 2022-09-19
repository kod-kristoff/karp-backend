import abc
import logging
from typing import List, Generic, Protocol, TypeVar, Any, Iterable, Type

import injector
import logging


logger = logging.getLogger(__name__)


T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)
T_contra = TypeVar("T_contra", contravariant=True)


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

    def collect_new_events(self) -> Iterable[Event]:
        return self._pending_domain_events[:]

    def clear_events(self) -> None:
        self._pending_domain_events.clear()


class EventHandler(Protocol[T_contra]):
    """Simple generic used to associate handlers with events using DI.

    e.g EventHandler[ResourceCreated].
    """

    def __call__(self, event: T_contra, *args: Any, **kwds: Any) -> Any:
        raise NotImplementedError()


class AsyncEventHandler(Protocol[T_contra]):
    """An async counterpart of EventHandler[Event]."""

    def __call__(self, event: T_contra, *args: Any, **kwds: Any) -> Any:
        raise NotImplementedError()


class EventHandlerProvider(injector.Provider):
    """Useful for configuring bind for event handlers.
    Using DI for dispatching events to handlers requires ability to bind multiple
    handlers to a single key (Handler[Event]).
    """

    def __init__(self, cls: Type[T]) -> None:
        self._cls = cls

    def get(self, container: injector.Injector) -> List[T]:
        return [container.create_object(self._cls)]  # type: ignore


class AsyncEventHandlerProvider(injector.Provider):
    """An async counterpart of EventHandlerProvider.
    In async, one does not need to actually construct the instance.
    It is enough to obtain class itself.
    """

    def __init__(self, cls: Type[T]) -> None:
        self._cls = cls

    def get(self, _container: injector.Injector) -> List[Type[T]]:
        return [self._cls]  # type: ignore


class EventBus(abc.ABC):
    @abc.abstractmethod
    def post(self, event: Event) -> None:
        raise NotImplementedError


class InjectorEventBus(EventBus):
    def __init__(self, container: injector.Injector) -> None:
        self._container = container

    def post(self, event: Event) -> None:
        logger.info("handling event sync", extra={"karp_event": event})
        try:
            evt_handlers = self._container.get(
                List[EventHandler[type(event)]]  # type: ignore
            )
        except injector.UnsatisfiedRequirement as err:
            logger.warning(
                "No event handler for event?",
                extra={"karp_event": event, "err_message": err},
            )
        else:
            for evt_handler in evt_handlers:
                logger.debug(
                    "handling event with handler",
                    extra={"karp_event": event, "evt_handler": evt_handler},
                )
                try:
                    evt_handler(event)
                except Exception as err:
                    logger.exception(
                        "Exception handling event", extra={"karp_event": event}
                    )
                    raise

        logger.info("handling event async", extra={"karp_event": event})
        try:
            evt_handlers = self._container.get(
                List[AsyncEventHandler[type(event)]]  # type: ignore
            )
        except injector.UnsatisfiedRequirement as err:
            logger.warning(
                "No async event handler for event?",
                extra={"karp_event": event, "err_message": err},
            )
        else:
            for async_handler in evt_handlers:
                logger.debug(
                    "handling event with handler",
                    extra={"karp_event": event, "evt_handler": async_handler},
                )
                try:
                    async_handler(event)
                except Exception as err:
                    logger.exception(
                        "Exception handling event", extra={"karp_event": event}
                    )
                    raise
