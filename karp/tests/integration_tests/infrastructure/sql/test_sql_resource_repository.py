"""Tests for SQLResourceRepository"""
# from karp.cli import publish_resource
from karp.services.resource_handlers import CreateResourceHandler
from karp.domain.commands.resource_commands import CreateResourceCommand
from karp.utility.unique_id import make_unique_id
import uuid

import pytest

from karp.domain.models.resource import ResourceOp, create_resource, Resource

from karp.domain.errors import IntegrityError

# from karp.domain.models.lexical_resource import LexicalResource
from karp.infrastructure.unit_of_work import unit_of_work
from karp.infrastructure.sql.sql_resource_repository import SqlResourceRepository
from karp.adapters.orm import SqlAlchemy, ResourceViewBuilder


# pytestmark = pytest.mark.usefixtures("db_setup")


# @pytest.fixture(name="resource_repo", scope="module")
# def fixture_resource_repo(db_setup_scope_module):
#     resource_repo = SqlResourceRepository()
#     return resource_repo


# def test_sql_resource_repo_empty(resource_repo):
#     with unit_of_work(using=resource_repo) as uw:
#         assert uw.resource_ids() == []
#         assert uw.history_by_resource_id("test_id") == []


def test_sql_resource_repo_put_resource():
    resource_id = make_unique_id()
    machine_name = "test_id"
    name = "Test"
    resource_config = {
        # "resource_id": resource_id,
        # "resource_name": resource_name,
        "a": "b",
    }
    user = "kristoff@example.com"
    message = "resource test_id added"

    db = SqlAlchemy("sqlite://")
    db.configure_mappings()
    db.recreate_schema()
    cmd = CreateResourceCommand(
        resource_id=resource_id,
        machine_name=machine_name,
        name=name,
        config=resource_config,
        message=message,
        created_by=user,
    )
    handler = CreateResourceHandler(db.unit_of_work_manager)
    handler.handle(cmd)
    # resource = create_resource(resource_config)

    expected_version = 1

    resources = db.get_session().query(Resource).all()

    assert len(resources) == 1

    resource = resources[0]
    # with unit_of_work(using=resource_repo) as uw:
    #     uw.put(resource)
    #     uw.commit()

    # with unit_of_work(using=resource_repo) as uw:
    #     assert uw.resource_ids() == [resource_id]

    assert resource.version == expected_version
    assert resource.message == message
    assert resource.op == ResourceOp.ADDED
    assert resource.last_modified_by == user

    view_builder = ResourceViewBuilder(db.get_session())
    resource_copy = view_builder.fetch(resource_id)

    assert resource_copy.id == resource_id
    assert isinstance(resource_copy, Resource)
    # with unit_of_work(using=resource_repo) as uw:
    #     resource_id_history = uw.history_by_resource_id(resource_id)
    #     assert len(resource_id_history) == 1

    # with unit_of_work(using=resource_repo) as uw:
    #     test_lex = uw.by_resource_id(resource_id)

    #     assert isinstance(test_lex, Resource)
    #     assert isinstance(test_lex.config, dict)
    #     assert test_lex.resource_id == resource_id
    #     assert test_lex.id == resource.id
    #     assert test_lex.name == resource_name
    #     assert test_lex.version == expected_version

    # # Update resource
    # with unit_of_work(using=resource_repo) as uw:
    #     resource.config["c"] = "added"
    #     resource.config["a"] = "changed"
    #     resource.is_published = True
    #     resource.stamp(user="Test user", message="change config")
    #     uw.update(resource)
    #     assert resource.version == 2

    # with unit_of_work(using=resource_repo) as uw:
    #     test_lex = uw.by_resource_id(resource_id)

    #     assert test_lex is not None
    #     assert test_lex.config["a"] == "changed"
    #     assert test_lex.config["c"] == "added"
    #     assert test_lex.is_published is True
    #     assert test_lex.version == 2
    #     assert uw.get_latest_version(resource_id) == test_lex.version

    # # Test history
    # with unit_of_work(using=resource_repo) as uw:
    #     resource_id_history = uw.history_by_resource_id(resource_id)

    #     assert len(resource_id_history) == 2
    #     assert resource_id_history[0].version == 2
    #     assert resource_id_history[1].version == 1


# def test_sql_resource_repo_put_lexical_resource(resource_repo):
#     resource_id = "test_id"
#     resource_name = "Test"
#     resource_config = {
#         "resource_id": resource_id,
#         "resource_name": resource_name,
#         "a": "b",
#     }
#     resource = Resource.create_resource("lexical_resource", resource_config)

#     expected_version = 1

#     with unit_of_work(using=resource_repo) as uw:
#         uw.put(resource)
#         uw.commit()
#         assert uw.resource_ids() == [resource_id]

#         assert resource.version == expected_version
#         assert resource.message == "Resource added."
#         assert resource.op == ResourceOp.ADDED
#         resource_id_history = uw.history_by_resource_id(resource_id)
#         assert len(resource_id_history) == 1

#     with unit_of_work(using=resource_repo) as uw:
#         test_lex = uw.resource_with_id_and_version(resource_id, expected_version)

#         assert isinstance(test_lex, Resource)
#         assert isinstance(test_lex, LexicalResource)
#         assert isinstance(test_lex.config, dict)
#         assert test_lex.resource_id == resource_id
#         assert test_lex.id == resource.id
#         assert test_lex.name == resource_name


def test_sql_resource_repo_putting_already_existing_resource_id_raises():  # resource_repo):
    #     resource_id = "test_id"
    #     resource_name = "Test"
    #     resource_config = {
    #         "resource_id": resource_id,
    #         "resource_name": resource_name,
    #         "a": "b",
    #     }
    resource_id = make_unique_id()
    machine_name = "test_id"
    name = "Test"
    resource_config = {
        # "resource_id": resource_id,
        # "resource_name": resource_name,
        "a": "b",
    }
    user = "kristoff@example.com"
    message = "resource test_id added"

    db = SqlAlchemy("sqlite://")
    db.configure_mappings()
    db.recreate_schema()
    cmd = CreateResourceCommand(
        resource_id=resource_id,
        machine_name=machine_name,
        name=name,
        config=resource_config,
        message=message,
        created_by=user,
    )
    handler = CreateResourceHandler(db.unit_of_work_manager)
    handler.handle(cmd)

    cmd2 = CreateResourceCommand(
        resource_id=resource_id,
        machine_name="test_id_2",
        name=name,
        config=resource_config,
        message=message,
        created_by=user,
    )

    with pytest.raises(IntegrityError) as exc_info:
        handler.handle(cmd2)


#     resource = create_resource(resource_config)

#     with unit_of_work(using=resource_repo) as uw:
#         uw.put(resource)
#         assert len(uw.resource_ids()) == 1
#         res = uw.by_resource_id(resource_id)

#         assert res.id == resource.id

#     resource = create_resource(
#         {"resource_id": resource_id, "resource_name": resource_name, "a": "b"}
#     )

#     with pytest.raises(IntegrityError) as exc_info:
#         with unit_of_work(using=resource_repo) as uw:
#             uw.put(resource)

#     assert "Resource with resource_id 'test_id' already exists." in str(exc_info)


# def test_sql_resource_repo_update_resource(resource_repo):
#     resource_id = "test_id"
#     resource_version = 1

#     expected_config = {"a": "b"}
#     resource_id = "test_id"
#     resource_name = "Test"
#     resource_config = {
#         "resource_id": resource_id,
#         "resource_name": resource_name,
#         "a": "b",
#     }
#     resource = create_resource(resource_config)

#     expected_version = 1

#     with unit_of_work(using=resource_repo) as uw:
#         uw.put(resource)
#         uw.commit()
#         assert uw.resource_ids() == [resource_id]

#         assert resource.version == expected_version
#         assert resource.message == "Resource added."
#         assert resource.op == ResourceOp.ADDED
#         resource_id_history = uw.history_by_resource_id(resource_id)
#         assert len(resource_id_history) == 1

#     with unit_of_work(using=resource_repo) as uw:
#         resource = uw.resource_with_id_and_version(resource_id, resource_version)

#         assert resource.config == expected_config
#         resource.config["c"] = "added"
#         resource.config["a"] = "changed"
#         resource.is_published = True
#         resource.stamp(user="Test user", message="change config")
#         uw.update(resource)
#         assert resource.version == 2

#     resource_version += 1

#     with unit_of_work(using=resource_repo) as uw:
#         lex = uw.by_resource_id(resource_id)

#         assert lex is not None
#         assert lex.resource_id == resource_id
#         assert lex.version == resource_version
#         assert uw.get_latest_version(resource_id) == resource_version


# def test_sql_resource_repo_put_another_version(resource_repo):
#     resource_id = "test_id"
#     resource_config = {
#         "resource_id": resource_id,
#         "resource_name": "Test",
#         "a": "b",
#     }
#     resource = create_resource(resource_config)

#     expected_version = 3
#     resource._version = 3

#     with unit_of_work(using=resource_repo) as uw:
#         uw.put(resource)

#         assert uw.resource_ids() == [resource_id]

#         assert resource.version == expected_version
#         assert not resource.is_published


# # def test_sql_resource_repo_put_yet_another_version(resource_repo):
# #     resource_id = "test_id"
# #     resource_config = {
# #         "resource_id": resource_id,
# #         "resource_name": "Test",
# #         "a": "b",
# #     }
# #     resource = create_resource(resource_config)

# #     expected_version = 3

# #     with unit_of_work(using=resource_repo) as uw:
# #         uw.put(resource)

# #         assert uw.resource_ids() == [resource_id]

# #         assert resource.version == expected_version
# #         assert not resource.is_published


# def test_sql_resource_repo_2nd_active_raises(resource_repo):
#     resource_id = "test_id"
#     resource_version = 2
#     with pytest.raises(Exception):
#         with unit_of_work(using=resource_repo) as uw:
#             resource = uw.resource_with_id_and_version(resource_id, resource_version)
#             resource.is_published = True
#             resource.stamp(user="Admin", message="make active")
#             uw.update(resource)
#             assert resource.is_published is True


# def test_sql_resource_repo_version_change_to_existing_raises(resource_repo):
#     resource_id = "test_id"
#     resource_version = 2
#     with pytest.raises(Exception):
#         with unit_of_work(using=resource_repo) as uw:
#             resource = uw.resource_with_id_and_version(resource_id, resource_version)
#             resource.version = 1


# def test_sql_resource_repo_put_another_resource(resource_repo):
#     resource_id = "test_id_2"
#     resource_config = {
#         "resource_id": resource_id,
#         "resource_name": "Test",
#         "fields": {"name": {"type": "string", "required": True}},
#     }

#     expected_version = 1

#     with unit_of_work(using=resource_repo) as uw:
#         resource = create_resource(resource_config)
#         resource.is_published = True
#         uw.put(resource)
#         uw.commit()

#         assert resource.version == expected_version

#         assert resource.is_published is True


# # def test_sql_resource_repo_deep_update_of_resource(resource_repo):
# #     with unit_of_work(using=resource_repo) as uw:
# #         resource = uw.get_active_resource("test_id_2")
# #         assert resource is not None

# #         resource.config["fields"]["count"] = {"type": "int"}
# #         resource.stamp(user="Admin", message="change")
# #         assert resource.is_published
# #         assert resource.version == 2
# #         uw.update(resource)
# #         # assert resource.name_id == "test_id_2Test 2"

# #     with unit_of_work(using=resource_repo) as uw:
# #         resource = uw.get_active_resource("test_id_2")

# #         assert resource is not None
# #         assert "count" in resource.config["fields"]
# #         assert resource.config["fields"]["count"] == {"type": "int"}


# # def test_get_published_resources(resource_repo):
# #     with unit_of_work(using=resource_repo) as uw:
# #         uw.put(create_resource({"resource_id": "test_id_3", "resource_name": "g"}))
# #         published_resources = uw.get_published_resources()

# #         assert len(published_resources) == 1
# #         assert published_resources[0].resource_id == "test_id_2"


# # def test_sql_resource_repo_
