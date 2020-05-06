from karp.domain.model.resource import ResourceRepository

# from karp.domain.services.auth import AuthenticationService
from karp.domain.services.search import SearchService
from karp.domain.services.indexmgr.index import IndexService


class Context:
    def __init__(
        self,
        resource_repo: ResourceRepository,
        search_service: SearchService,
        index_service: IndexService,
        # auth_service: AuthenticationService,
    ):
        self.resource_repo = resource_repo
        self.search_service = search_service
        self.index_service = index_service
        # self.auth_service = auth_service
