from karp.domain.model.resource import ResourceRepository
from karp.domain.model.entry import EntryRepositoryFactory
from karp.domain.services.auth import AuthenticationService
from karp.domain.services.search import SearchService


class Context:
    def __init__(
        self,
        resource_repo: ResourceRepository,
        entry_repo_factory: EntryRepositoryFactory,
        search_service: SearchService,
        auth_service: AuthenticationService,
    ):
        self.resource_repo = resource_repo
        self.entry_repo_factory = entry_repo_factory
        self.search_service = search_service
        self.auth_service = auth_service
