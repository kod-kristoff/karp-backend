from elasticsearch import Elasticsearch  # pyre-ignore
from .index import EsIndex

# from .search import EsSearch
# import karp.search.search


def init_es(host):
    es = Elasticsearch(
        hosts=host,
        sniff_on_start=True,
        sniff_on_connection_fail=True,
        sniffer_timeout=60,
        sniff_timeout=10,
    )
    index_module = EsIndex(es)
    # search_module = EsSearch(es)
    # karp.search.search.init(search_module)
    from karp.indexmgr import indexer

    indexer.init(index_module)
