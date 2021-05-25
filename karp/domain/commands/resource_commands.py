from typing import Dict
from pydantic import BaseModel

from karp.utility.unique_id import UniqueId


class CreateResourceCommand(BaseModel):
    resource_id: UniqueId
    machine_name: str
    name: str
    config: Dict
    message: str
    created_by: str
