from elasticsearch import Elasticsearch  # pyre-ignore
from .index import EsIndex
from .es_search import Es6SearchService
from karp import search
from karp.domain.services.indexmgr import indexer


def init_es(host):
    print("Setting up ES with host={}".format(host))
    es = Elasticsearch(
        hosts=host,
        sniff_on_start=True,
        sniff_on_connection_fail=True,
        sniffer_timeout=60,
        sniff_timeout=10,
    )
    index_module = EsIndex(es)
    search_module = Es6SearchService(es, index_module)
    search.init(search_module)
    indexer.init(index_module)
    return index_module, search_module
