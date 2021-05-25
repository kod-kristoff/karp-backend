from typing import Dict, Optional

from pydantic import BaseModel

from karp.domain import repository
from karp.utility.unique_id import UniqueId

# pylint: disable=unsubscriptable-object
class Command(BaseModel):
    pass


class CreateResource(Command):
    resource_id: UniqueId
    machine_name: str
    name: str
    config: Dict
    message: str
    created_by: str
    entries: Optional[repository.EntryRepository] = None

    class Config:
        arbitrary_types_allowed = True


class CreateEntry(Command):
    resource_id: UniqueId
    entry_id: UniqueId
    name: str
    body: Dict
    message: str
    created_by: str
