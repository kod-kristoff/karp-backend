from karp import elasticsearch as es


class SQLwES6:
    def __init__(self, app):
        _es = es.Elasticsearch(
                hosts=app.config['ELASTICSEARCH_HOST'],
                sniff_on_start=True,
                sniff_on_connection_fail=True,
                sniffer_timeout=60,
                sniff_timeout=10
                )
        self.search_service = es.EsSearch(_es)
        self.index_service = es.EsIndex(_es)
        self.auth_service = None
        self.resource_def_repo = None
        self.resource_repo = None


class SQL:
    def __init__(self, app):
        self.search_service = None
        self.index_service = None
        self.auth_service = None
        self.resource_def_repo = None
        self.resource_repo = None
