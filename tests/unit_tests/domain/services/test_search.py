from karp.domain.services.search import (
#    create_query,
    Query,
#    StatsQuery,
)


def test_create_query_creates_query():
    resource_str = "test"
    # query = create_query(resource_str)
    query = Query()

    assert isinstance(query, Query)
    # assert isinstance(query, StatsQuery)

    assert len(query.resources) == 1
    assert query.resources[0] == resource_str
