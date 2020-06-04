"""Tests for SQLResourceRepository"""
from unittest import mock
import uuid

import pytest

from karp.domain.model.entry_repository import EntryRepository
from karp.domain.model.resource import (
    ResourceCategory,
    ResourceOp,
    create_resource,
    Resource,
)
from karp.domain.model.lexical_resource import LexicalResource

from karp.domain.services.resource import init_resource

from karp.infrastructure.unit_of_work import unit_of_work
from karp.infrastructure.sql.resource_repository import SqlResourceRepository
from karp.infrastructure.sql import entry_repository


db_uri = "sqlite:///"


@pytest.fixture(name="resource_repo", scope="session")
def fixture_resource_repo():
    resource_repo = SqlResourceRepository(db_uri)
    return resource_repo


def test_sql_resource_repo_empty(resource_repo):
    assert resource_repo.db_uri == db_uri
    with unit_of_work(using=resource_repo) as uw:
        assert uw.resource_ids() == []
        assert uw.history_by_resource_id("test_id") == []


def test_sql_resource_repo_put_resource(resource_repo):
    resource_id = "test_id"
    resource_name = "Test"
    resource_config = {
        "resource_id": resource_id,
        "resource_name": resource_name,
        "a": "b",
    }
    resource = Resource.create_resource(None, None, resource_config)

    expected_version = 1

    with unit_of_work(using=resource_repo) as uw:
        uw.put(resource)
        uw.commit()
        assert uw.resource_ids() == [resource_id]

        assert resource.version == expected_version
        assert resource.message == "Resource added."
        assert resource.op == ResourceOp.ADDED
        resource_id_history = uw.history_by_resource_id(resource_id)
        assert len(resource_id_history) == 1

    with unit_of_work(using=resource_repo) as uw:
        test_lex = uw.resource_with_id_and_version(resource_id, expected_version)

        assert isinstance(test_lex, Resource)
        assert isinstance(test_lex.config, dict)
        assert test_lex.resource_id == resource_id
        assert test_lex.id == resource.id
        assert test_lex.name == resource_name


def test_sql_resource_repo_put_lexical_resource(resource_repo):
    resource_id = "test_lex_id"
    resource_name = "Test"
    resource_config = {
        "resource_id": resource_id,
        "resource_name": resource_name,
        "a": "b",
    }
    entry_repository_mock = mock.MagicMock(
        spec=EntryRepository, type="repository_type", id=uuid.uuid4()
    )
    with mock.patch(
        "karp.domain.model.entry_repository.EntryRepository.get_default_repository_type",
        return_value="entry_repository_type",
    ), mock.patch(
        "karp.domain.model.entry_repository.EntryRepository.create_repository_settings",
        return_value={},
    ), mock.patch(
        "karp.domain.model.entry_repository.EntryRepository.create",
        return_value=entry_repository_mock,
    ):
        resource = Resource.create_resource(
            ResourceCategory.LEXICAL_RESOURCE, "lexical_resource_v1", resource_config
        )

    expected_version = 1

    with unit_of_work(using=resource_repo) as uw:
        uw.put(resource)
        uw.commit()
        assert resource_id in uw.resource_ids()

        assert resource.version == expected_version
        assert resource.message == "Resource added."
        assert resource.op == ResourceOp.ADDED
        assert resource.entry_repository_id == str(entry_repository_mock.id)
        resource_id_history = uw.history_by_resource_id(resource_id)
        assert len(resource_id_history) == 1

    with unit_of_work(using=resource_repo) as uw:
        test_lex = uw.resource_with_id_and_version(resource_id, expected_version)

        assert isinstance(test_lex, Resource)
        assert isinstance(test_lex, LexicalResource)
        assert isinstance(test_lex.config, dict)
        assert test_lex.resource_id == resource_id
        assert test_lex.id == resource.id
        assert test_lex.name == resource_name


def test_sql_resource_repo_lexical_resource_with_entry_repository(resource_repo):
    with unit_of_work(using=resource_repo) as uw:
        entry_repository_settings = {
            "db_uri": "sqlite:///",
            "table_name": "random",
        }
        entry_repository = EntryRepository.create("sql_v1", entry_repository_settings)

        uw.put(entry_repository)
        uw.commit()

        resource_settings = {
            "resource_id": "test_lex_2",
            "resource_name": "Test lex 2",
            "entry_repository_id": str(entry_repository.id),
        }
        lexical_resource = LexicalResource.create_resource(
            None, None, resource_settings
        )

        uw.put(lexical_resource)
        uw.commit()

        init_resource(lexical_resource, resource_repo)

        assert lexical_resource.entry_repository.id == entry_repository.id


def test_sql_resource_repo_update_resource(resource_repo):
    resource_id = "test_id"
    resource_version = 1

    expected_config = {"a": "b"}

    with unit_of_work(using=resource_repo) as uw:
        resource = uw.resource_with_id_and_version(resource_id, resource_version)

        assert resource.config == expected_config
        resource.config["c"] = "added"
        resource.config["a"] = "changed"
        resource.is_published = True
        resource.stamp(user="Test user", message="change config")
        uw.update(resource)
        assert resource.version == 2

    resource_version += 1

    with unit_of_work(using=resource_repo) as uw:
        test_lex = uw.resource_with_id_and_version(resource_id, resource_version)

        assert test_lex is not None
        assert test_lex.config["a"] == "changed"
        assert test_lex.config["c"] == "added"
        assert test_lex.is_published is True

    with unit_of_work(using=resource_repo) as uw:
        lex = uw.get_active_resource(resource_id)

        assert lex is not None
        assert lex.resource_id == resource_id
        assert lex.version == resource_version
        assert uw.get_latest_version(resource_id) == resource_version


def test_sql_resource_repo_put_another_version(resource_repo):
    resource_id = "test_id"
    resource_config = {
        "resource_id": resource_id,
        "resource_name": "Test",
        "a": "b",
    }
    resource = create_resource(resource_config)

    resource._version = 3

    with unit_of_work(using=resource_repo) as uw:
        uw.put(resource)

        assert uw.resource_ids() == [resource_id, "test_lex_id"]

        expected_version = 3
        assert resource.version == expected_version
        assert not resource.is_published


# def test_sql_resource_repo_put_yet_another_version(resource_repo):
#     resource_id = "test_id"
#     resource_config = {
#         "resource_id": resource_id,
#         "resource_name": "Test",
#         "a": "b",
#     }
#     resource = create_resource(resource_config)

#     expected_version = 3

#     with unit_of_work(using=resource_repo) as uw:
#         uw.put(resource)

#         assert uw.resource_ids() == [resource_id]

#         assert resource.version == expected_version
#         assert not resource.is_published


def test_sql_resource_repo_2nd_active_raises(resource_repo):
    with pytest.raises(Exception):
        with unit_of_work(using=resource_repo) as uw:
            resource_id = "test_id"
            resource_version = 2
            resource = uw.resource_with_id_and_version(resource_id, resource_version)
            resource.is_published = True
            resource.stamp(user="Admin", message="make active")
            uw.update(resource)
            assert resource.is_published is True


def test_sql_resource_repo_version_change_to_existing_raises(resource_repo):
    with pytest.raises(Exception):
        with unit_of_work(using=resource_repo) as uw:
            resource_id = "test_id"
            resource_version = 2
            resource = uw.resource_with_id_and_version(resource_id, resource_version)
            resource.version = 1


def test_sql_resource_repo_put_another_resource(resource_repo):
    with unit_of_work(using=resource_repo) as uw:
        resource_id = "test_id_2"
        resource_config = {
            "resource_id": resource_id,
            "resource_name": "Test",
            "fields": {"name": {"type": "string", "required": True}},
        }

        resource = create_resource(resource_config)
        resource.is_published = True
        uw.put(resource)
        uw.commit()

        expected_version = 1

        assert resource.version == expected_version

        assert resource.is_published is True


# def test_sql_resource_repo_deep_update_of_resource(resource_repo):
#     with unit_of_work(using=resource_repo) as uw:
#         resource = uw.get_active_resource("test_id_2")
#         assert resource is not None

#         resource.config["fields"]["count"] = {"type": "int"}
#         resource.stamp(user="Admin", message="change")
#         assert resource.is_published
#         assert resource.version == 2
#         uw.update(resource)
#         # assert resource.name_id == "test_id_2Test 2"

#     with unit_of_work(using=resource_repo) as uw:
#         resource = uw.get_active_resource("test_id_2")

#         assert resource is not None
#         assert "count" in resource.config["fields"]
#         assert resource.config["fields"]["count"] == {"type": "int"}


def test_get_published_resources(resource_repo):
    with unit_of_work(using=resource_repo) as uw:
        uw.put(create_resource({"resource_id": "test_id_3", "resource_name": "g"}))
        published_resources = uw.get_published_resources()

        assert len(published_resources) == 1
        assert published_resources[0].resource_id == "test_id_2"
