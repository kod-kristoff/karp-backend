import json

# import json_streams

from karp.domain.models.entry import EntryRepository, create_entry

from karp.domain.services.entries import add_entries

from karp.infrastructure.sql import entry_repository
from karp.infrastructure.unit_of_work import unit_of_work

from tests.integration_tests.common_fixtures import fixture_places
from tests import common_data


def test_service_add_entries_works(places):
    assert isinstance(places.entry_repository, EntryRepository)
    with unit_of_work(using=places.entry_repository) as uw:
        assert len(uw.entry_ids()) == 0

    entries = []
    for raw_entry in common_data.PLACES:
        entries.append(places.create_entry_from_dict(raw_entry))
    add_entries(places, entries)

    with unit_of_work(using=places.entry_repository) as uw:
        assert len(uw.entry_ids()) == 9
