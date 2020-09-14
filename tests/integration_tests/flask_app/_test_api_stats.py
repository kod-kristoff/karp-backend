import pytest  # pyre-ignore

from tests.utils import get_json


@pytest.mark.parametrize("endpoint", ["stats"])
@pytest.mark.parametrize("field", [("name"),])
def test_stats_api_for_places(client_with_entries_scope_session, field, endpoint):
    path = f"places/{endpoint}/{field}"
    result = get_json(client_with_entries_scope_session, path)

    assert len(result) == 9
