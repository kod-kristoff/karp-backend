import pytest

from karp.domain.model.resource import Resource, ResourceCategory
import karp.domain.model.lexical_resource

from karp.infrastructure.sql.resource_repository import SqlResourceRepository
import karp.infrastructure.sql.entry_repository


@pytest.fixture(scope="session")
def resource_repo():
    resource_repo = SqlResourceRepository("sqlite:///")
    return resource_repo


def test_create_resource(resource_repo):
    config = {
        "resource_id": "test_resource_3"
    }
    resource = Resource.create_resource(
        ResourceCategory.LEXICAL_RESOURCE,
        "lexical_resource_v1",
        config
    )
    assert resource is not None
