"""Handle of unique ids."""

from typing import Any, Optional, Union
import uuid

import ulid
import ulid.codec

UniqueId = ulid.ULID
UniqueIdType = ulid.ULID
typing_UniqueId = ulid.ULID


def make_unique_id(t: Optional[ulid.codec.TimestampPrimitive] = None) -> UniqueId:
    """Generate an UniqueId that are sortable.

    >>> from karp_lex.value_objects import make_unique_id
    >>> from datetime import datetime
    >>> old_id = make_unique_id(datetime(1999,12,31,23,59,59))
    >>> make_unique_id() > old_id
    True
    """
    return ulid.new() if t is None else ulid.from_timestamp(t)


def to_unique_id(phrase: Any) -> UniqueId:
    if isinstance(phrase, str):
        return ulid.from_str(phrase)
    raise ValueError()


parse = ulid.parse


class UniqueIdStr(str):
    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(examples=["01BJQMF54D093DXEAWZ6JYRPAQ"])

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, UniqueId):
            return str(v)
        elif not isinstance(v, str):
            raise TypeError("string or UniqueId required")

        if len(v) != 26:
            raise ValueError("invalid uniqueid format")

        return cls(v)

    def __repr__(self) -> str:
        return f"UniqueIdStr({super().__repr__()})"


UniqueIdPrimitive = Union[ulid.api.api.ULIDPrimitive, UniqueIdStr]
