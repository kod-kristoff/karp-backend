
from typing import List


def create_query(resource_str: str):
    query = Query(resources=resource_str.split(","))
    return query


class Query:
    def __init__(self, resources: List[str]) -> None:
        self.resources = resources


class StatsQuery(Query):
    pass
