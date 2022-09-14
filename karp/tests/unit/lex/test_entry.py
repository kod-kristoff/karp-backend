from copy import copy
from typing import Dict

import pytest

from karp.lex.domain import errors, events
from karp.lex.domain import entities
from karp.foundation.value_objects import unique_id
from karp.tests import common_data

from karp.tests.unit.lex import factories


def random_entry(entry_id: str = None, body: Dict = None):
    return entities.create_entry(
        entity_id=unique_id.make_unique_id(),
        repo_id=unique_id.make_unique_id(),
        entry_id=entry_id or "a",
        body=body or {},
        message="add",
        last_modified_by="kristoff@example.com",
        last_modified=12345.67,
    )


def test_new_entry_has_event():
    entry, domain_events = random_entry()
    assert domain_events[-1] == events.EntryAdded(
        entity_id=entry.id,
        entry_id=entry.entry_id,
        repo_id=entry.repo_id,
        body=entry.body,
        user=entry.last_modified_by,
        timestamp=entry.last_modified,
        message=entry.message,
    )


def test_discarded_entry_has_event():
    entry, _ = random_entry()
    domain_events = entry.discard(
        user="alice@example.org",
        message="bad",
        timestamp=123.45,
    )
    assert entry.discarded
    assert domain_events[-1] == events.EntryDeleted(
        entity_id=entry.id,
        entry_id=entry.entry_id,
        repo_id=entry.repo_id,
        user=entry.last_modified_by,
        timestamp=entry.last_modified,
        message=entry.message,
        version=2,
    )


# def test_resource_create_entry_from_raw():
#     resource = create_resource(
#         {
#             "resource_id": "places",
#             "resource_name": "Platser i Sverige",
#             "fields": {
#                 "name": {"type": "string", "required": True},
#                 "municipality": {
#                     "collection": True,
#                     "type": "number",
#                     "required": True,
#                 },
#                 "population": {"type": "number"},
#                 "area": {"type": "number"},
#                 "density": {"type": "number"},
#                 "code": {"type": "number", "required": True},
#             },
#             "sort": "name",
#             "id": "code",
#         }
#     )
#
#     entry = entry_lifecycle.create_entry_from_dict(resource, common_data.PLACES[0])
#
#     assert isinstance(entry, Entry)
#     assert entry.entry_id == "1"
