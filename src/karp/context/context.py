"""Standard contexts."""
from typing import Optional

from karp import elasticsearch as es
from karp import search
from karp import resourcemgr


class ResourceRepository:
    def get_by_id(
        self, resource_id: str, version: Optional[int] = None
    ) -> resourcemgr.Resource:
        return resourcemgr.get_resource(resource_id, version=version)


class SQLwES6:
    def __init__(self, app):
        _es = es.Elasticsearch(
            hosts=app.config["ELASTICSEARCH_HOST"],
            sniff_on_start=True,
            sniff_on_connection_fail=True,
            sniffer_timeout=60,
            sniff_timeout=10,
        )
        self.search = es.EsSearch(_es)
        self.index_service = es.EsIndex(_es)
        self.auth_service = None
        self.resource_def_repo = None
        self.resource_repo = ResourceRepository()


class SQL:
    def __init__(self, app):
        self.search = search.SearchInterface()
        self.index_service = None
        self.auth_service = None
        self.resource_def_repo = None
        self.resource_repo = ResourceRepository()
