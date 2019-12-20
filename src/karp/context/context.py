from karp import elasticsearch as es


class SQLwES6:
    def __init__(self):
        self.auth_service = None
        self.search_service = None
        self.index_service = None
        self.resource_def_repo = None
        self.resource_repo = None

    def init(self, app):
        print(f"host= {app.config['ELASTICSEARCH_HOST']}")
        _es = es.Elasticsearch(
            hosts=app.config["ELASTICSEARCH_HOST"],
            sniff_on_start=True,
            sniff_on_connection_fail=True,
            sniffer_timeout=60,
            sniff_timeout=10,
        )
        self.search_service = es.EsSearch(_es)
        self.index_service = es.EsIndex(_es)
