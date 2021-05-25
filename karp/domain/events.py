from dataclasses import dataclass
from karp.utility.unique_id import UniqueId


class Event:
    pass


@dataclass
class ResourceCreated(Event):
    resource_id: UniqueId
