import abc
from typing import Iterable, Optional

import pydantic

from karp.foundation.value_objects import UniqueId


class ResourceDto(pydantic.BaseModel):
    resource_id: str
    entity_id: UniqueId
    is_published: bool
    version: int
    name: str
    last_modified_by: str
    message: str
    last_modified: float
    config: dict
    entry_repository_id: UniqueId
    discarded: bool


class GetPublishedResources(abc.ABC):
    @abc.abstractmethod
    def query(self) -> Iterable[ResourceDto]:
        pass


class GetResources(abc.ABC):
    @abc.abstractmethod
    def query(self) -> Iterable[ResourceDto]:
        pass


class GetEntryRepositoryId(abc.ABC):
    @abc.abstractmethod
    def query(self, resource_id: str) -> UniqueId:
        raise NotImplementedError()


class ReadOnlyResourceRepository(abc.ABC):
    def get_by_resource_id(
        self, resource_id: str, version: Optional[int] = None
    ) -> Optional[ResourceDto]:
        resource = self._get_by_resource_id(resource_id)
        if not resource:
            return None

        if version is not None:
            resource = self.get_by_id(resource.entity_id, version=version)
        return resource

    @abc.abstractmethod
    def get_by_id(
        self, entity_id: UniqueId, version: Optional[int] = None
    ) -> Optional[ResourceDto]:
        pass

    @abc.abstractmethod
    def _get_by_resource_id(self, resource_id: str) -> Optional[ResourceDto]:
        pass

    @abc.abstractmethod
    def get_published_resources(self) -> Iterable[ResourceDto]:
        pass
