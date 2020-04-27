from unittest import mock

import pytest

from karp.domain.errors import DiscardedEntityError
from karp.domain.model.entry import Entry, EntryOp


def test_entry_create():
    entry_id = "test..1"
    body = {"test": "test"}
    with mock.patch("karp.utility.time.utc_now", return_value=12345):
        entry = Entry(entry_id, body)

    assert isinstance(entry, Entry)

    expected_id = None

    assert entry.id == expected_id
    assert entry.version == 0
    assert entry.entry_id == entry_id
    assert entry.body == body

    assert int(entry.last_modified) == 12345
    assert entry.last_modified_by == "Unknown user"

    assert entry.op == EntryOp.ADDED
    assert entry.message == "Entry added."


@pytest.mark.parametrize("field,value", [("entry_id", "new..1"), ("body", {"b": "r"}),])
def test_entry_update_updates(field, value):
    entry = Entry("test..2", {"a": ["1", "e"]})

    assert entry.version == 0
    previous_last_modified = entry.last_modified
    previous_last_modified_by = entry.last_modified_by
    message = f"Updated {field}"

    user = "Test User"

    setattr(entry, field, value)
    entry.stamp(user=user, message=message)

    assert getattr(entry, field) == value
    assert entry.last_modified > previous_last_modified
    assert entry.last_modified_by != previous_last_modified_by
    assert entry.last_modified_by == user
    assert entry.op == EntryOp.UPDATED
    assert entry.message == message
    assert entry.version == 1


@pytest.mark.parametrize("field,value", [
    ("entry_id", "new..1"),
    ("body", {"b": "r"}),
])
def test_entry_update_of_discarded_raises_(field, value):
    entry = Entry("test..2", {"a": ["1", "e"]})

    assert entry.version == 0
    previous_last_modified = entry.last_modified

    entry.discard(user="Admin")

    assert entry.discarded
    assert entry.version == 1
    assert entry.last_modified > previous_last_modified
    assert entry.last_modified_by == "Admin"
    assert entry.op == EntryOp.DELETED
    assert entry.message == "Entry deleted."

    with pytest.raises(DiscardedEntityError):
        setattr(entry, field, value)
