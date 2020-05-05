"""Lexicon"""
import abc
import enum
from typing import Dict, Any, Optional

from karp.domain.model.entity import TimestampedVersionedEntity
from karp.domain.model.events import DomainEvent
from karp.utility import unique_id


class LexiconOp(enum.Enum):
    ADDED = "ADDED"
    UPDATED = "UPDATED"
    DELETED = "DELETED"


class Lexicon(TimestampedVersionedEntity):
    class Stamped(TimestampedVersionedEntity.Stamped):
        def mutate(self, obj):
            super().mutate(obj)
            obj._message = self.message
            obj._op = LexiconOp.UPDATED

    def __init__(
        self,
        lexicon_id: str,
        name: str,
        config: Dict[str, Any],
        message: str,
        op: LexiconOp,
        *args,
        is_active: bool = False,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._lexicon_id = lexicon_id
        self._name = name
        self.is_active = is_active
        self.config = config
        self._message = message
        self._op = op

    @property
    def lexicon_id(self):
        return self._lexicon_id

    @property
    def name(self):
        return self._name

    @property
    def message(self):
        return self._message

    @property
    def op(self):
        return self._op

    def stamp(self, *, user: str, message: str = None, increment_version: bool = True):
        self._check_not_discarded()
        event = Lexicon.Stamped(
            entity_id=self.id,
            entity_version=self.version,
            entity_last_modified=self.last_modified,
            user=user,
            message=message,
            increment_version=increment_version,
        )
        event.mutate(self)


def create_lexicon(config: Dict) -> Lexicon:
    lexicon_id = config.pop("lexicon_id")
    lexicon_name = config.pop("lexicon_name")
    lexicon = Lexicon(
        lexicon_id,
        lexicon_name,
        config,
        message="Lexicon added.",
        op=LexiconOp.ADDED,
        entity_id=unique_id.make_unique_id(),
        version=1,
    )
    return lexicon


# ===== Repository =====


class Repository(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def put(self, lexicon: Lexicon):
        raise NotImplementedError()

    @abc.abstractmethod
    def lexicon_ids(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def lexicons_with_id(self, lexicon_id: str):
        raise NotImplementedError()

    @abc.abstractmethod
    def lexicon_with_id_and_version(self, lexicon_id: str, version: int):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_active_lexicon(self, lexicon_id: str) -> Optional[Lexicon]:
        raise NotImplementedError()
