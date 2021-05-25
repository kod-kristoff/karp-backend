import abc
from typing import Set
from karp.adapters import orm
from karp.domain import model


class ResourceRepository(abc.ABC):
    def __init__(self):
        self.seen: Set[model.Resource] = set()

    def add(self, resource: model.Resource):
        self._add(resource)
        self.seen.add(resource)

    def get(self, sku) -> model.Resource:
        resource = self._get(sku)
        if resource:
            self.seen.add(resource)
        return resource

    # def get_by_batchref(self, batchref) -> model.Resource:
    #     resource = self._get_by_batchref(batchref)
    #     if resource:
    #         self.seen.add(resource)
    #     return resource

    @abc.abstractmethod
    def _add(self, resource: model.Resource):
        raise NotImplementedError

    @abc.abstractmethod
    def _get(self, sku) -> model.Resource:
        raise NotImplementedError

    # @abc.abstractmethod
    # def _get_by_batchref(self, batchref) -> model.Resource:
    #     raise NotImplementedError


class EntryRepository(abc.ABC):
    def __init__(self):
        self.seen: Set[model.Entry] = set()

    def add(self, entry: model.Entry):
        self._add(entry)
        self.seen.add(entry)

    def get(self, sku) -> model.Entry:
        entry = self._get(sku)
        if entry:
            self.seen.add(entry)
        return entry

    # def get_by_batchref(self, batchref) -> model.Resource:
    #     entry = self._get_by_batchref(batchref)
    #     if entry:
    #         self.seen.add(entry)
    #     return entry

    @abc.abstractmethod
    def _add(self, entry: model.Entry):
        raise NotImplementedError

    @abc.abstractmethod
    def _get(self, sku) -> model.Entry:
        raise NotImplementedError


# class SqlAlchemyRepository(ResourceRepository):
#     def __init__(self, session):
#         super().__init__()
#         self.session = session

#     def _add(self, entry):
#         self.session.add(entry)

#     def _get(self, sku):
#         return self.session.query(model.Resource).filter_by(sku=sku).first()

#     def _get_by_batchref(self, batchref):
#         return (
#             self.session.query(model.Resource)
#             .join(model.Batch)
#             .filter(
#                 orm.batches.c.reference == batchref,
#             )
#             .first()
#         )
