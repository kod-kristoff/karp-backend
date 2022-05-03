import pytest
from starlette import status

from karp.foundation.value_objects import unique_id
from karp.webapp.schemas import ResourceCreate


pytestmark = pytest.mark.asyncio


@pytest.fixture
def new_resource() -> ResourceCreate:
    return ResourceCreate(
        resource_id='test_resource',
        name='Test resource',
        user='test@exampl.com',
        message='test',
        config={
            'fields': {
                'foo': {'type': 'string'}
            },
            'id': 'foo',
        },
        entry_repo_id=unique_id.make_unique_id(),
    )


class TestResourcesRoutes:
    async def test_get_routes_exist(self, client):
        response = await client.get("/resources")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    async def test_post_routes_exist(self, client):
        response = await client.post("/resources")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    async def test_invalid_dats_returns_422(self, client):
        response = await client.post("/resources", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestCreateResource:
    async def test_valid_input_creates_resource(
        self,
        client,
        new_resource: ResourceCreate,
    ):
        data = new_resource.dict()
        data['entry_repo_id'] = str(new_resource.entry_repo_id)
        response = await client.post('/resources', json=data)
        assert response.status_code == status.HTTP_201_CREATED

        response_data = response.json()
        created_resource = ResourceCreate(
            user=response_data['last_modified_by'],
            **response_data,
        )
        assert created_resource == new_resource


class TestGetResource:
    async def test_get_resource_by_resource_id(self, client):
        response = await client.get('/resources/test_resource')
        assert response.status_code == status.HTTP_200_OK

        resource =
