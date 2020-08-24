from elasticsearch import Elasticsearch  # pyre-ignore
from karp.infrastructure.elasticsearch6.es_search_index import EsSearchIndex
from karp import app


def init_es(host):
    print("Setting up ES with host={}".format(host))
    es = Elasticsearch(
        hosts=host,
        sniff_on_start=True,
        sniff_on_connection_fail=True,
        sniffer_timeout=60,
        sniff_timeout=10,
    )
    es_search_index = EsSearchIndex(es)
    app.config.init_search_index(es_search_index)
