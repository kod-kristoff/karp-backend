import pytest

from karp.application.services import entries, resources

from tests.common_data import MUNICIPALITIES, PLACES
from tests.utils import get_json, add_entries


@pytest.fixture(scope="module", name="fa_stats_data_client")
def fixture_fa_stats_data_client(fa_client_w_places_w_municipalities_scope_module):
    add_entries(
        fa_client_w_places_w_municipalities_scope_module,
        {"places": PLACES, "municipalities": MUNICIPALITIES},
    )

    return fa_client_w_places_w_municipalities_scope_module


def test_stats(fa_stats_data_client):
    response = fa_stats_data_client.get(
        "places/stats/area",
        headers={"Authorization": "Bearer 1234"},
    )
    assert response.status_code == 200

    entries = response.json()

    assert len(entries) == 4
