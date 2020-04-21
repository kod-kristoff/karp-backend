"""Lexicon"""
from typing import Dict, Any

from karp.domain.model.entity import VersionedEntity


class Lexicon(VersionedEntity):
    def __init__(
        self,
        lexicon_id: str,
        name: str,
        config: Dict[str, Any],
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._lexicon_id = lexicon_id
        self._name = name
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
        config,        entity_id=None,
        version=None,
    )
    return lexicon
