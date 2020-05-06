import elasticsearch

from karp.application.context import Context
from karp.application.config import Config

from karp.infrastructure import elasticsearch6
from karp.infrastructure.elasticsearch6.es_search import Es6SearchService
from karp.infrastructure.sql.resource_repository import SqlResourceRepository


class SqlEs6Context(Context):
    def __init__(self, config: Config):

        index_service, search_service = elasticsearch6.init_es(
            config.ELASTICSEARCH_HOST
        )
        super().__init__(
            resource_repo=SqlResourceRepository(config.SQLALCHEMY_DATABASE_URI),
            search_service=search_service,
            index_service=index_service,
        )
