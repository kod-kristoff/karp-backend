from dataclasses import dataclass
from typing import Dict
import uuid


@dataclass
class Event:
    timestamp: float


@dataclass
class ResourceCreated(Event):
    id: uuid.UUID
    resource_id: str
    name: str
    config: Dict
    user: str
    message: str


@dataclass
class ResourceUpdated(Event):
    id: uuid.UUID
    resource_id: str
    version: int
    name: str
    config: Dict
    user: str
    message: str
