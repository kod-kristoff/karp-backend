import time
import pytest  # pyre-ignore

from tests.utils import get_json


@pytest.mark.parametrize("endpoint", ["stats"])
@pytest.mark.parametrize("field", [("name"),])
def test_stats_api_for_places(client_with_entries_scope_module, field, endpoint):
    time.sleep(5)
    path = f"places/{endpoint}/{field}"
    result = get_json(client_with_entries_scope_module, path)
    print(f"result = {result}")
    assert len(result) == 9
