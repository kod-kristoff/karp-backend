from tests.utils import get_json


def test_get_entries_after_10000(client_with_entries_scope_session):
    resource_id = "large_lex"
    response = get_json(
        client_with_entries_scope_session, f"/query/{resource_id}?from=11000"
    )

    assert response["hits"]["total"] == 12000
    assert len(response["hits"]["hits"]) == 25
