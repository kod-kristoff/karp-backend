import json

import pytest

from karp.domain.models.resource import create_resource
from karp.domain.models.entry import EntryRepository, create_entry

from karp.infrastructure.sql import entry_repository
from karp.infrastructure.unit_of_work import unit_of_work

from tests import common_data


@pytest.fixture
def places():
    with open("tests/data/config/places.json") as fp:
        places_config = json.load(fp)

    resource = create_resource(places_config)

    yield resource

    resource.entry_repository.teardown()


def test_places_has_entry_repository(places):
    assert isinstance(places.entry_repository, EntryRepository)
    with unit_of_work(using=places.entry_repository) as uw:
        assert len(uw.entry_ids()) == 0


def test_places_search_by_referencable(places):
    assert isinstance(places.entry_repository, EntryRepository)
    with unit_of_work(using=places.entry_repository) as uw:
        for entry_dict in common_data.PLACES:
            entry = create_entry(str(entry_dict["code"]), entry_dict)
            uw.put(entry)
        uw.commit()

        assert len(uw.entry_ids()) == 9

        entry_copies = uw.by_referencable(larger_place=7)

        assert len(entry_copies) == 1
        entry_copy = entry_copies[0]

        assert entry_copy.entry_id == "1"

        assert len(uw.by_referencable(municipality=1)) == 2
        assert len(uw.by_referencable(municipality=2)) == 5
        assert len(uw.by_referencable(municipality=3)) == 5
