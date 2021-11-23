import abc
import typing

import pydantic
from sb_json_tools import jsondiff

from karp import errors as karp_errors
from karp.foundation.value_objects import unique_id
from karp.lex.application.repositories import ResourceUnitOfWork, EntryUowRepositoryUnitOfWork
from karp.lex.domain.entities.entry import EntryOp


# pylint: disable=unsubscriptable-object
class EntryDto(pydantic.BaseModel):
    entry_id: str
    entry_uuid: unique_id.UniqueId
    resource: str
    version: int
    entry: typing.Dict
    last_modified: float
    last_modified_by: str


class EntryDiffRequest(pydantic.BaseModel):
    resource_id: str
    entry_id: str
    from_version: typing.Optional[int] = None
    to_version: typing.Optional[int] = None
    from_date: typing.Optional[float] = None
    to_date: typing.Optional[float] = None
    entry: typing.Optional[typing.Dict] = None


class EntryHistoryRequest(pydantic.BaseModel):
    resource_id: str
    user_id: typing.Optional[str] = None
    entry_id: typing.Optional[str] = None
    from_date: typing.Optional[float] = None
    to_date: typing.Optional[float] = None
    from_version: typing.Optional[int] = None
    to_version: typing.Optional[int] = None
    current_page: int = 0
    page_size: int = 100


class EntryDiffDto(pydantic.BaseModel):
    diff: typing.Any
    from_version: typing.Optional[int]
    to_version: typing.Optional[int]


class HistoryDto(pydantic.BaseModel):
    timestamp: float
    message: str
    entry_id: str
    version: int
    op: EntryOp
    user_id: str
    diff: typing.Dict


class GetEntryDiff(abc.ABC):
    @abc.abstractmethod
    def query(self, req: EntryDiffRequest) -> EntryDiffDto:
        pass


class GetEntryHistory(abc.ABC):
    @abc.abstractmethod
    def query(
        self,
        resource_id: str,
        entry_id: str,
        version: typing.Optional[int],
    ) -> EntryDto:
        pass


class GetHistory(abc.ABC):
    @abc.abstractmethod
    def query(
        self,
        req: EntryHistoryRequest
    ) -> typing.Tuple[typing.List[HistoryDto], int]:
        pass


class EntryViews(abc.ABC):
    @abc.abstractmethod
    def get_by_id(
        self,
        resource_id: str,
        entry_uuid: unique_id.UniqueId,
    ) -> EntryDto:
        pass

    @abc.abstractmethod
    def get_by_entry_id(
        self,
        resource_id: str,
        entry_id: str,
    ) -> EntryDto:
        pass

    @abc.abstractmethod
    def get_total(self, resource_id: str) -> int:
        pass
