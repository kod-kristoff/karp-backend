from typing import Optional, Union, List

from karp.domain.models.resource import Resource
from karp.domain.ports import ResourceRepository, UnitOfWorkManager, UnitOfWork
from karp.utility.unique_id import UniqueId


# pylint: disable=unsubscriptable-object


class FakeResourceRepository(ResourceRepository):
    def __init__(self):
        self.resources = []

    def put(self, resource):
        self.resources.append(resource)

    def get(self, id):
        return self.resources[id]

    def __len__(self):
        return len(self.resources)

    def __getitem__(self, idx):
        return self.resources[idx]

    def by_id(
        self, id: Union[UniqueId, str], *, version: Optional[int]
    ) -> Optional[Resource]:
        return super().by_id(id, version=version)

    def by_resource_id(
        self, resource_id: str, *, version: Optional[int]
    ) -> Optional[Resource]:
        return super().by_resource_id(resource_id, version=version)

    def resource_ids(self) -> List[Resource]:
        return super().resource_ids()

    def resource_with_id_and_version(self, resource_id: str, version: int):
        return super().resource_with_id_and_version(resource_id, version)

    def get_active_resource(self, resource_id: str) -> Optional[Resource]:
        return super().get_active_resource(resource_id)

    def resources_with_id(self, resource_id: str):
        return super().resources_with_id(resource_id)

    def get_published_resources(self) -> List[Resource]:
        return super().get_published_resources()


class FakeUnitOfWork(UnitOfWork, UnitOfWorkManager):
    def __init__(self):
        self._resources = FakeResourceRepository()

    def start(self):
        self.was_committed = False
        self.was_rolled_back = False
        return self

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.exn_type = type
        self.exn = value
        self.traceback = traceback

    def commit(self):
        self.was_committed = True

    def rollback(self):
        self.was_rolled_back = True

    @property
    def resources(self):
        return self._resources
