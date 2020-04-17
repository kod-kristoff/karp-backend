"""Lexicon"""
from typing import Dict

from karp.domain.model.entity import VersionedEntity


class Lexicon(VersionedEntity):
    pass


def create_lexicon(config: Dict) -> Lexicon:
    lexicon = Lexicon(entity_id=None)
    return lexicon
