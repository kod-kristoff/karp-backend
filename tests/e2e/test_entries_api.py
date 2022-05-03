import pytest
from starlette import status


pytestmark = pytest.mark.asyncio


class TestEntriesRoutes:
    async def test_routes_exist(self, client):
        response = await client.post('/entries/places')
        assert response.status_code != status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize("invalid_data", [
        ({},),
        ({"user": "a@b.se"},),
    ])
    async def test_invalid_data_returns_422(self, client, invalid_data):
        response = await client.post("/entries/places", json=invalid_data)
        print(f'{response.json()=}')
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
