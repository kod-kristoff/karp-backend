from datetime import datetime
from typing import TypeVar, Generic, Optional
import uuid

from pydantic import root_validator
from pydantic.generics import GenericModel

from karp_lex_core.value_objects import UniqueIdStr

T = TypeVar("T")


def to_lower_camel(s: str) -> str:
    return "".join(
        word.capitalize() if i > 0 else word for i, word in enumerate(s.split("_"))
    )


class EntryDto(GenericModel, Generic[T]):
    entry: T
    last_modified_by: str
    last_modified: datetime
    entity_id: Optional[UniqueIdStr]
    message: str
    version: Optional[int]
    discarded: bool = False

    class Config:
        extra = "forbid"
        alias_generator = to_lower_camel

    @root_validator(pre=True)
    @classmethod
    def allow_snake_case(cls, values):
        if "last_modified" in values:
            values["lastModified"] = values.pop("last_modified")
        if "last_modified_by" in values:
            values["lastModifiedBy"] = values.pop("last_modified_by")
        if "entity_id" in values:
            values["entityId"] = values.pop("entity_id")
        return values
