from typing import Optional
from karp.domain.models.search_index import SearchIndex


class Config:
    def __init__(self) -> None:
        self.search_index = None

    def init_search_index(self, search_index: Optional[SearchIndex]):
        self.search_index = search_index
