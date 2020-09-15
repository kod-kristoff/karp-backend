import json

import pytest


from karp.domain.models.resource import create_resource

from karp.application import ctx
from karp.infrastructure.unit_of_work import unit_of_work


@pytest.fixture(name="places")
def fixture_places():
    with open("tests/data/config/places.json") as fp:
        places_config = json.load(fp)

    resource = create_resource(places_config)

    yield resource

    resource.entry_repository.teardown()


@pytest.fixture(name="fa_client_w_places")
def fixture_fa_client_w_places(fa_client, places):
    with unit_of_work(using=ctx.resource_repo) as uw:
        uw.put(places)

    return fa_client
