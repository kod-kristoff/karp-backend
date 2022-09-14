import uuid
from typing import Dict

from pydantic import BaseModel

from karp.foundation import events, time
from karp.foundation.value_objects import unique_id
from karp.lex.domain.events import base


class ResourceCreated(base.DomainEvent):
    entity_id: unique_id.UniqueId
    resource_id: str
    entry_repo_id: unique_id.UniqueId
    name: str
    config: Dict
    user: str
    message: str


class ResourceLoaded(base.DomainEvent):
    entity_id: unique_id.UniqueId
    resource_id: str
    name: str
    config: Dict
    user: str
    message: str
    version: int


class ResourceDiscarded(base.DomainEvent):
    entity_id: unique_id.UniqueId
    resource_id: str
    name: str
    config: Dict
    user: str
    message: str
    version: int


class ResourcePublished(base.DomainEvent):
    entity_id: unique_id.UniqueId
    resource_id: str
    entry_repo_id: unique_id.UniqueId
    version: int
    name: str
    config: Dict
    user: str
    message: str


class ResourceUpdated(base.DomainEvent):
    entity_id: unique_id.UniqueId
    resource_id: str
    entry_repo_id: unique_id.UniqueId
    version: int
    name: str
    config: Dict
    user: str
    message: str


class EntryAdded(base.DomainEvent):
    entity_id: unique_id.UniqueId
    repo_id: unique_id.UniqueId
    entry_id: str
    body: Dict
    message: str
    user: str


class EntryUpdated(base.DomainEvent):
    entity_id: unique_id.UniqueId
    repo_id: unique_id.UniqueId
    entry_id: str
    body: Dict
    message: str
    user: str
    version: int


class EntryIdChanged(EntryUpdated):
    old_entry_id: str


class EntryDeleted(base.DomainEvent):
    entity_id: unique_id.UniqueId
    repo_id: unique_id.UniqueId
    entry_id: str
    version: int
    message: str
    user: str
