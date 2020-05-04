"""Lexicon"""
import abc
from typing import Dict, Any, Optional

from karp.domain.model.entity import TimestampedVersionedEntity
from karp.utility import unique_id


class Lexicon(TimestampedVersionedEntity):
    def __init__(
        self,
        lexicon_id: str,
        name: str,
        config: Dict[str, Any],
        *args,
        is_active: bool = False,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._lexicon_id = lexicon_id
        self._name = name
        self.is_active = is_active
        self.config = config

    @property
    def lexicon_id(self):
        return self._lexicon_id

    @property
    def name(self):
        return self._name


def create_lexicon(config: Dict) -> Lexicon:
    lexicon_id = config.pop("lexicon_id")
    lexicon_name = config.pop("lexicon_name")
    lexicon = Lexicon(
        lexicon_id,
        lexicon_name,
        config,
        entity_id=unique_id.make_unique_id(),
        version=None,
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
