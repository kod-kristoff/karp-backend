import pytest

from tests.utils import get_json


@pytest.mark.parametrize(
    "resource",
    [
        "places",
        "municipalities",
        "large_lex",
    ],
)
def test_resources_contains(client_with_entries_scope_session, resource):
    result = get_json(client_with_entries_scope_session, "/resources")

    assert any(filter(lambda entry: entry["resource_id"] == resource, result))
