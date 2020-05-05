"""Tests for SQLLexiconRepository"""
import uuid

import pytest

from karp.domain.model.lexicon import create_lexicon, Lexicon
from karp.infrastructure.unit_of_work import unit_of_work
from karp.infrastructure.sql.lexicon_repository import SqlLexiconRepository


db_uri = "sqlite:///"


@pytest.fixture(name="lexicon_repo", scope="session")
def fixture_lexicon_repo():
    lexicon_repo = SqlLexiconRepository(db_uri)
    return lexicon_repo


def test_sql_lexicon_repo_empty(lexicon_repo):
    assert lexicon_repo.db_uri == db_uri
    with unit_of_work(using=lexicon_repo) as uw:
        assert uw.lexicon_ids() == []
        assert uw.history_by_lexicon_id("test_id") == []


def test_sql_lexicon_repo_put(lexicon_repo):
    lexicon_id = "test_id"
    lexicon_name = "Test"
    lexicon_config = {
        "lexicon_id": lexicon_id,
        "lexicon_name": lexicon_name,
        "a": "b",
    }
    lexicon = create_lexicon(lexicon_config)

    expected_version = 1

    with unit_of_work(using=lexicon_repo) as uw:
        uw.put(lexicon)
        uw.commit()
        assert uw.lexicon_ids() == [lexicon_id]

        assert lexicon.version == expected_version
        lexicon_id_history = uw.history_by_lexicon_id(lexicon_id)
        assert len(lexicon_id_history) == 1

    with unit_of_work(using=lexicon_repo) as uw:
        test_lex = uw.lexicon_with_id_and_version(lexicon_id, expected_version)

        assert isinstance(test_lex, Lexicon)
        assert isinstance(test_lex.config, dict)
        assert test_lex.lexicon_id == lexicon_id
        assert test_lex.id == lexicon.id
        assert test_lex.name == lexicon_name


def test_sql_lexicon_repo_update_lexicon(lexicon_repo):
    lexicon_id = "test_id"
    lexicon_version = 1

    expected_config = {"a": "b"}

    with unit_of_work(using=lexicon_repo) as uw:
        lexicon = uw.lexicon_with_id_and_version(lexicon_id, lexicon_version)

        assert lexicon.config == expected_config
        lexicon.config["c"] = "added"
        lexicon.config["a"] = "changed"
        lexicon.is_active = True
        lexicon.stamp(user="Test user")
        uw.update(lexicon)

    with unit_of_work(using=lexicon_repo) as uw:
        test_lex = uw.lexicon_with_id_and_version(lexicon_id, lexicon_version)

        assert test_lex.config["a"] == "changed"
        assert test_lex.config["c"] == "added"
        assert test_lex.is_active is True

    with unit_of_work(using=lexicon_repo) as uw:
        lex = uw.get_active_lexicon(lexicon_id)

        assert lex is not None
        assert lex.lexicon_id == lexicon_id
        assert lex.version == lexicon_version
        assert uw.get_latest_version(lexicon_id) == lexicon_version


def test_sql_lexicon_repo_put_another_version(lexicon_repo):
    lexicon_id = "test_id"
    lexicon_config = {
        "lexicon_id": lexicon_id,
        "lexicon_name": "Test",
        "a": "b",
    }
    lexicon = create_lexicon(lexicon_config)

    expected_version = 2

    with unit_of_work(using=lexicon_repo) as uw:
        uw.put(lexicon)

        assert uw.lexicon_ids() == [lexicon_id]

        assert lexicon.version == expected_version
        assert not lexicon.is_active


def test_sql_lexicon_repo_put_yet_another_version(lexicon_repo):
    lexicon_id = "test_id"
    lexicon_config = {
        "lexicon_id": lexicon_id,
        "lexicon_name": "Test",
        "a": "b",
    }
    lexicon = create_lexicon(lexicon_config)

    expected_version = 3

    with unit_of_work(using=lexicon_repo) as uw:
        uw.put(lexicon)

        assert uw.lexicon_ids() == [lexicon_id]

        assert lexicon.version == expected_version
        assert not lexicon.is_active


def test_sql_lexicon_repo_2nd_active_raises(lexicon_repo):
    lexicon_id = "test_id"
    lexicon_version = 2
    with pytest.raises(Exception):
        with unit_of_work(using=lexicon_repo) as uw:
            lexicon = uw.lexicon_with_id_and_version(lexicon_id, lexicon_version)
            lexicon.is_active = True
            assert lexicon.is_active is True


def test_sql_lexicon_repo_version_change_to_existing_raises(lexicon_repo):
    lexicon_id = "test_id"
    lexicon_version = 2
    with pytest.raises(Exception):
        with unit_of_work(using=lexicon_repo) as uw:
            lexicon = uw.lexicon_with_id_and_version(lexicon_id, lexicon_version)
            lexicon.version = 1


def test_sql_lexicon_repo_put_another_lexicon(lexicon_repo):
    lexicon_id = "test_id_2"
    lexicon_config = {
        "lexicon_id": lexicon_id,
        "lexicon_name": "Test",
        "fields": {"name": {"type": "string", "required": True}},
    }

    expected_version = 1

    with unit_of_work(using=lexicon_repo) as uw:
        lexicon = create_lexicon(lexicon_config)
        uw.put(lexicon)
        uw.commit()

        assert lexicon.version == expected_version

        lexicon.is_active = True
        uw.commit()

        assert lexicon.is_active is True


def test_sql_lexicon_repo_deep_update_of_lexicon(lexicon_repo):
    with unit_of_work(using=lexicon_repo) as uw:
        lexicon = uw.get_active_lexicon("test_id_2")

        lexicon.config["fields"]["count"] = {"type": "int"}
        # assert lexicon.name_id == "test_id_2Test 2"

    with unit_of_work(using=lexicon_repo) as uw:
        lexicon = uw.get_active_lexicon("test_id_2")

        assert "count" in lexicon.config["fields"]
        assert lexicon.config["fields"]["count"] == {"type": "int"}
