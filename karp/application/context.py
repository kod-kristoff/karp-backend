from typing import Optional
from karp.domain.models.search_index import SearchIndex


class Context:
    def __init__(self) -> None:
        self.search_index = SearchIndex()

    def init_search_index(self, search_index: SearchIndex):
        self.search_index = search_index
