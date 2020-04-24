from unittest import mock

import pytest

from karp.domain.errors import DiscardedEntityError
from karp.domain.model.history_entry import HistoryEntry


def test_history_entry_create():
    entry_id = "test..1"
    body = {"test": "test"}
    with mock.patch("karp.utility.time.utc_now", return_value=12345):
        entry = HistoryEntry(entry_id, body)

    assert isinstance(entry, HistoryEntry)

    assert entry.id == None
    assert entry.version == 0
    assert entry.entry_id == entry_id
    assert entry.body == body

    assert int(entry.last_modified) == 12345
    assert entry.last_modified_by == "Unknown user"


@pytest.mark.parametrize("field,value", [("entry_id", "new..1"), ("body", {"b": "r"}),])
def test_history_entry_update_updates(field, value):
    entry = HistoryEntry("test..2", {"a": ["1", "e"]})

    assert entry.version == 0

    setattr(entry, field, value)

    assert getattr(entry, field) == value


@pytest.mark.parametrize("field,value", [("entry_id", "new..1"), ("body", {"b": "r"}),])
def test_history_entry_update_of_discarded_raises_(field, value):
    entry = HistoryEntry("test..2", {"a": ["1", "e"]})

    assert entry.version == 0
    previous_last_modified = entry.last_modified

    entry.discard(user="Admin")

    assert entry.discarded
    assert entry.version == 1
    assert entry.last_modified > previous_last_modified
    assert entry.last_modified_by == "Admin"

    with pytest.raises(DiscardedEntityError):
        setattr(entry, field, value)
