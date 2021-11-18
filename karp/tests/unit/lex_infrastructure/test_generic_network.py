from karp.lex.domain.entities.entry import create_entry
from karp.foundation.value_objects import unique_id
from karp.lex_infrastructure.queries import generic_network

from karp.tests.unit.lex import factories


def test__create_ref():
    resource_id = "resource_id"
    resource_version = 1
    _id = 5
    entry_id = "entry_id"
    entry_body = {"body": {"of": "entry"}}
    entry = factories.EntryFactory(entry_id=entry_id, body=entry_body)

    ref = generic_network._create_ref(resource_id, resource_version, entry)

    assert ref["resource_id"] == resource_id
    assert ref["resource_version"] == resource_version
    # assert ref["entry"]["id"] == _id
    assert ref["entry"].entry_id == entry_id
    assert ref["entry"].body == entry_body
