from karp.application.context import SqlEs6Context

from karp.infrastructure.elasticsearch6.search_service import Es6SearchService
from karp.infrastructure.sql.resource_repository import SqlResourceRepository
from karp.infrastructure.sql.entry_repository_factory import SqlEntryRepositoryFactory


def test_sql_es6_context_create():
    context = SqlEs6Context()

    assert isinstance(context.resource_repo, SqlResourceRepository)
    assert isinstance(context.entry_repo_factory, SqlEntryRepositoryFactory)
    assert isinstance(context.search_service, Es6SearchService)

