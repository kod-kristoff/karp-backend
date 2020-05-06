from karp.application.config import Config
from karp.infrastructure.context.sql_es6_context import SqlEs6Context

from karp.infrastructure.elasticsearch6.es_search import Es6SearchService
from karp.infrastructure.sql.resource_repository import SqlResourceRepository


def test_sql_es6_context_create():
    context = SqlEs6Context(Config())

    assert isinstance(context.resource_repo, SqlResourceRepository)
    assert isinstance(context.search_service, Es6SearchService)
