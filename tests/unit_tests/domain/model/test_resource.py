from unittest import mock
import uuid

import pytest

from karp.domain.errors import ConsistencyError, DiscardedEntityError, ConstraintsError
from karp.domain.model.lexicon import Lexicon, LexiconOp, Release, create_lexicon


def test_create_lexicon_creates_lexicon():
    lexicon_id = "test_lexicon"
    name = "Test lexicon"
    conf = {
        "lexicon_id": lexicon_id,
        "lexicon_name": name,
        "sort": ["baseform"],
        "fields": {"baseform": {"type": "string", "required": True}},
    }
    with mock.patch("karp.utility.time.utc_now", return_value=12345):
        lexicon = create_lexicon(conf)

    assert isinstance(lexicon, Lexicon)
    assert lexicon.id == uuid.UUID(str(lexicon.id), version=4)
    assert lexicon.version == 1
    assert lexicon.lexicon_id == lexicon_id
    assert lexicon.name == name
    assert not lexicon.discarded
    assert not lexicon.is_active
    assert "lexicon_id" not in lexicon.config
    assert "lexicon_name" not in lexicon.config
    assert "sort" in lexicon.config
    assert lexicon.config["sort"] == conf["sort"]
    assert "fields" in lexicon.config
    assert lexicon.config["fields"] == conf["fields"]
    assert int(lexicon.last_modified) == 12345
    assert lexicon.message == "Lexicon added."
    assert lexicon.op == LexiconOp.ADDED


def test_lexicon_stamp_changes_last_modified_and_version():
    lexicon_id = "test_lexicon"
    name = "Test lexicon"
    conf = {
        "lexicon_id": lexicon_id,
        "lexicon_name": name,
        "sort": ["baseform"],
        "fields": {"baseform": {"type": "string", "required": True}},
    }
    lexicon = create_lexicon(conf)

    previous_last_modified = lexicon.last_modified
    previous_version = lexicon.version

    lexicon.stamp(user="Test")

    assert lexicon.last_modified > previous_last_modified
    assert lexicon.last_modified_by == "Test"
    assert lexicon.version == (previous_version + 1)


def test_lexicon_add_new_release_creates_release():
    lexicon = create_lexicon(
        {
            "lexicon_id": "test_lexicon",
            "lexicon_name": "Test lexicon",
            "sort": ["baseform"],
            "fields": {"baseform": {"type": "string", "required": True}},
        }
    )

    previous_last_modified = lexicon.last_modified

    lexicon.add_new_release(name="v1.0.0", user="Admin", description="")

    assert len(lexicon.releases) == 1
    assert lexicon.releases[0].name == "v1.0.0"
    assert lexicon.releases[0].publication_date == lexicon.last_modified
    assert lexicon.releases[0].description == ""
    assert lexicon.releases[0].root.id == lexicon.id
    assert lexicon.last_modified > previous_last_modified
    assert lexicon.last_modified_by == "Admin"
    assert lexicon.message == "Release 'v1.0.0' created."
    assert lexicon.version == 2


def test_lexicon_release_with_name_on_discarded_raises_discarded_entity_error():
    lexicon = create_lexicon(
        {
            "lexicon_id": "test_lexicon",
            "lexicon_name": "Test lexicon",
            "sort": ["baseform"],
            "fields": {"baseform": {"type": "string", "required": True}},
        }
    )

    lexicon.discard(user="Test", message="Discard")

    assert lexicon.discarded

    with pytest.raises(DiscardedEntityError):
        lexicon.release_with_name("test")


def test_lexicon_add_new_release_on_discarded_raises_discarded_entity_error():
    lexicon = create_lexicon(
        {
            "lexicon_id": "test_lexicon",
            "lexicon_name": "Test lexicon",
            "sort": ["baseform"],
            "fields": {"baseform": {"type": "string", "required": True}},
        }
    )

    lexicon.discard(user="Test", message="Discard")

    assert lexicon.discarded

    with pytest.raises(DiscardedEntityError):
        lexicon.add_new_release(name="test", user="TEST", description="")


def test_lexicon_add_new_release_with_invalid_name_raises_constraints_error():
    lexicon = create_lexicon(
        {
            "lexicon_id": "test_lexicon",
            "lexicon_name": "Test lexicon",
            "sort": ["baseform"],
            "fields": {"baseform": {"type": "string", "required": True}},
        }
    )

    with pytest.raises(ConstraintsError):
        lexicon.add_new_release(name="", user="Test", description="")


def test_lexicon_new_release_added_with_wrong_version_raises_consistency_error():
    lexicon = create_lexicon(
        {
            "lexicon_id": "test_lexicon",
            "lexicon_name": "Test lexicon",
            "sort": ["baseform"],
            "fields": {"baseform": {"type": "string", "required": True}},
        }
    )
    event = Lexicon.NewReleaseAdded(entity_id=lexicon.id, entity_version=12,)
    with pytest.raises(ConsistencyError):
        event.mutate(lexicon)


def test_lexicon_new_release_added_with_wrong_last_modified_raises_consistency_error():
    lexicon = create_lexicon(
        {
            "lexicon_id": "test_lexicon",
            "lexicon_name": "Test lexicon",
            "sort": ["baseform"],
            "fields": {"baseform": {"type": "string", "required": True}},
        }
    )
    event = Lexicon.NewReleaseAdded(
        entity_id=lexicon.id, entity_version=lexicon.version, entity_last_modified=2
    )
    with pytest.raises(ConsistencyError):
        event.mutate(lexicon)


def test_release_created_has_id():
    release = Release(
        entity_id="e", name="e-name", publication_date=12345.0, description="ee"
    )

    assert release.id == "e"
    assert release.name == "e-name"
    assert release.publication_date == 12345.0
    assert release.description == "ee"
    assert release.root.id == release.id


def test_release_created_w_lexicon_has_id():
    lexicon = create_lexicon(
        {
            "lexicon_id": "test_lexicon",
            "lexicon_name": "Test lexicon",
            "sort": ["baseform"],
            "fields": {"baseform": {"type": "string", "required": True}},
        }
    )
    release = Release(
        entity_id="e",
        name="e-name",
        publication_date=12345.0,
        description="ee",
        aggregate_root=lexicon,
    )

    assert release.id == "e"
    assert release.name == "e-name"
    assert release.publication_date == 12345.0
    assert release.description == "ee"
    assert release.root.id == lexicon.id
