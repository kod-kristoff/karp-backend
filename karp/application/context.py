from functools import singledispatch
from karp.application.config import Config
from karp.domain.model.resource import ResourceRepository

from karp.domain.services.auth.auth import Auth
from karp.domain.services.search import SearchService
from karp.domain.services.indexmgr.index import IndexService


class Context:
    def __init__(
        self,
        resource_repo: ResourceRepository = None,
        search_service: SearchService = None,
        index_service: IndexService = None,
        authentication_service: Auth = None
        # auth_service: AuthenticationService,
    ):
        self.resource_repo = resource_repo
        self.search_service = search_service
        self.index_service = index_service
        self.auth_service = authentication_service
        # self.auth_service = auth_service

    def __repr__(self):
        return f"Context(resource_repo={self.resource_repo!r})"


@singledispatch
def create_context(config: Config) -> Context:
    return Context()
