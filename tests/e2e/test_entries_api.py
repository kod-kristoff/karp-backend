from typing import Dict, List  # noqa: I001

import pytest
from fastapi import status

from karp import auth
from karp.main.errors import ClientErrorCodes
from karp.lex.application.queries.resources import GetEntryRepositoryId
from karp.lex.application.repositories.entry_repositories import (
    EntryUowRepositoryUnitOfWork,
)
from karp.timings import utc_now
from karp.lex_core.value_objects import (
    make_unique_id,
    unique_id,
)
from karp.lex.application.queries import EntryDto


def get_entry_uow(container, resource_id: str):  # noqa: ANN201
    get_entry_repository_id = container.get(GetEntryRepositoryId)  # type: ignore [misc]
    entry_repo_id = get_entry_repository_id.query("places")
    entry_uow_repo_uow = container.get(EntryUowRepositoryUnitOfWork)  # type: ignore [misc]
    with entry_uow_repo_uow as uw:
        return uw.repo.get_by_id(entry_repo_id)


def init(
    client,
    entries: List[Dict],
    access_token: auth.AccessToken,
) -> list[str]:
    result = []
    for entry in entries:
        response = client.put(
            "/entries/places",
            json={"entry": entry},
            headers=access_token.as_header(),
        )
        assert response.status_code < 300, response.status_code
        result.append(response.json()["newID"])
    return result


@pytest.fixture(name="entry_places_214_id", scope="session")
def fixture_entry_places_214_id(  # noqa: ANN201
    fa_data_client,
    write_token: auth.AccessToken,
):
    ids = init(
        fa_data_client,
        [
            {"code": 214, "name": "last_modified1", "municipality": [1]},
        ],
        write_token,
    )
    return ids[0]


@pytest.fixture(name="entry_places_209_id", scope="session")
def fixture_entry_places_209_id(  # noqa: ANN201
    fa_data_client,
    write_token: auth.AccessToken,
):
    ids = init(
        fa_data_client,
        [
            {"code": 209, "name": "a", "municipality": [1]},
        ],
        write_token,
    )
    return ids[0]


class TestEntriesRoutes:
    def test_routes_exist(self, fa_data_client):  # noqa: ANN201
        response = fa_data_client.post("/entries/places")
        assert response.status_code != status.HTTP_404_NOT_FOUND

        response = fa_data_client.put("/entries/places")
        assert response.status_code != status.HTTP_404_NOT_FOUND


class TestAddEntry:
    def test_put_route_exist(self, fa_data_client):  # noqa: ANN201
        response = fa_data_client.put("/entries/places")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize(
        "invalid_data",
        [
            ({},),
            ({"user": "a@b.se"},),
        ],
    )
    def test_invalid_data_returns_422(  # noqa: ANN201
        self,
        fa_data_client,
        invalid_data: Dict,
        write_token: auth.AccessToken,
    ):
        response = fa_data_client.put(
            "/entries/places",
            json=invalid_data,
            headers=write_token.as_header(),
        )
        print(f"{response.json()=}")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_add_with_valid_data_returns_201(  # noqa: ANN201
        self,
        fa_data_client,
        write_token: auth.AccessToken,
    ):
        response = fa_data_client.put(
            "/entries/places",
            json={
                "entry": {
                    "code": 203,
                    "name": "add203",
                    "population": 4,
                    "area": 50000,
                    "density": 5,
                    "municipality": [2, 3],
                }
            },
            headers=write_token.as_header(),
        )
        print(f"response. = {response.json()}")
        assert response.status_code == 201
        response_data = response.json()
        assert "newID" in response_data
        new_id = unique_id.parse(response_data["newID"])

        entry_uow = get_entry_uow(
            fa_data_client.app.state.app_context.container, resource_id="places"
        )
        with entry_uow as uw:
            assert new_id in uw.repo.entity_ids()

    def test_add_with_valid_data_and_entity_id_returns_201(  # noqa: ANN201
        self,
        fa_data_client,
        write_token: auth.AccessToken,
    ):
        entity_id = make_unique_id()
        response = fa_data_client.put(
            "/entries/places",
            json={
                "entry": {
                    "code": 2078,
                    "name": "add203",
                    "population": 4,
                    "area": 50000,
                    "density": 5,
                    "municipality": [2, 3],
                },
                "id": str(entity_id),
            },
            headers=write_token.as_header(),
        )
        print(f"response. = {response.json()}")
        assert response.status_code == 201
        response_data = response.json()
        assert "newID" in response_data
        new_id = response_data["newID"]

        entry_uow = get_entry_uow(
            fa_data_client.app.state.app_context.container, resource_id="places"
        )
        with entry_uow as uw:
            assert new_id in uw.repo.entity_ids()

    @pytest.mark.skip(reason="we don't use entry_id")
    def test_adding_existing_fails_with_400(  # noqa: ANN201
        self,
        fa_data_client,
        write_token: auth.AccessToken,
    ):
        entry_id = 204
        entry_name = f"add{entry_id}"
        response = fa_data_client.put(
            "/entries/places",
            json={
                "entry": {
                    "code": entry_id,
                    "name": entry_name,
                    "population": 4,
                    "area": 50000,
                    "density": 5,
                    "municipality": [2, 3],
                }
            },
            headers=write_token.as_header(),
        )
        print(f"response = {response.json()}")

        assert response.status_code == 201

        response = fa_data_client.put(
            "/entries/places",
            json={
                "entry": {
                    "code": entry_id,
                    "name": entry_name,
                    "population": 4,
                    "area": 50000,
                    "density": 5,
                    "municipality": [2, 3],
                }
            },
            headers=write_token.as_header(),
        )
        assert response.status_code == 400
        response_data = response.json()

        assert "error" in response_data
        assert "errorCode" in response_data
        assert ClientErrorCodes.DB_INTEGRITY_ERROR == response_data["errorCode"]
        assert (
            response_data["error"]
            == f"An entry with entry_id '{entry_id}' already exists."
        )

    def test_add_fails_with_invalid_entry(  # noqa: ANN201
        self,
        fa_data_client,
        write_token: auth.AccessToken,
    ):
        response = fa_data_client.put(
            "/entries/places", json={"entry": {}}, headers=write_token.as_header()
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data["errorCode"] == ClientErrorCodes.ENTRY_NOT_VALID

        # assert (
        #     response_data["error"] == "Missing ID field for resource 'places' in '{}'"
        # )


class TestDeleteEntry:
    def test_delete(  # noqa: ANN201
        self,
        fa_data_client,
        write_token: auth.AccessToken,
    ):
        entry_id = 205
        entry_name = f"delete{entry_id}"
        response = fa_data_client.put(
            "/entries/places",
            json={
                "entry": {
                    "code": entry_id,
                    "name": entry_name,
                    "population": 4,
                    "area": 50000,
                    "density": 5,
                    "municipality": [2, 3],
                }
            },
            headers=write_token.as_header(),
        )

        entity_id = response.json()["newID"]
        response = fa_data_client.delete(
            f"/entries/places/{entity_id}/1", headers=write_token.as_header()
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        entry_uow = get_entry_uow(
            fa_data_client.app.state.app_context.container, resource_id="places"
        )
        with entry_uow as uw:
            assert uw.repo.by_id(entity_id).discarded
            assert entity_id not in uw.repo.entity_ids()

    def test_delete_non_existing_fails(  # noqa: ANN201
        self,
        fa_data_client,
        write_token: auth.AccessToken,
    ):
        entry_id = make_unique_id()

        response = fa_data_client.delete(
            f"/entries/places/{entry_id}/3", headers=write_token.as_header()
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

        response_data = response.json()

        assert response_data["errorCode"] == ClientErrorCodes.ENTRY_NOT_FOUND

        assert (
            response_data["error"]
            == f"Entry '{entry_id}' not found in resource 'places' (version=latest)"
        )


class TestDeleteEntryRest:
    def test_delete_rest(  # noqa: ANN201
        self,
        fa_data_client,
        write_token: auth.AccessToken,
    ):
        entry_id = 205
        entry_name = f"delete{entry_id}"
        response = fa_data_client.put(
            "/entries/places",
            json={
                "entry": {
                    "code": entry_id,
                    "name": entry_name,
                    "population": 4,
                    "area": 50000,
                    "density": 5,
                    "municipality": [2, 3],
                }
            },
            headers=write_token.as_header(),
        )

        entity_id = response.json()["newID"]
        response = fa_data_client.delete(
            f"/entries/places/{entity_id}/1", headers=write_token.as_header()
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        entry_uow = get_entry_uow(
            fa_data_client.app.state.app_context.container, resource_id="places"
        )
        with entry_uow as uw:
            assert uw.repo.by_id(entity_id).discarded
            assert entity_id not in uw.repo.entity_ids()

    def test_delete_rest_non_existing_fails(  # noqa: ANN201
        self,
        fa_data_client,
        write_token: auth.AccessToken,
    ):
        entry_id = "00000000000000000000000000"

        response = fa_data_client.delete(
            f"/entries/places/{entry_id}/2", headers=write_token.as_header()
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

        response_data = response.json()

        assert response_data["errorCode"] == ClientErrorCodes.ENTRY_NOT_FOUND

        assert (
            response_data["error"]
            == f"Entry '{entry_id}' not found in resource 'places' (version=latest)"
        )


class TestUpdateEntry:
    def test_update_non_existing_fails(  # noqa: ANN201
        self,
        fa_data_client,
        write_token: auth.AccessToken,
    ):
        entry_id = make_unique_id()
        response = fa_data_client.post(
            f"/entries/places/{entry_id}",
            json={
                "entry": {
                    "code": 3,
                    "name": "test3",
                    "population": 5,
                    "area": 50000,
                    "density": 5,
                    "municipality": [2, 3],
                },
                "message": "changes",
                "version": 1,
            },
            headers=write_token.as_header(),
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_data = response.json()
        assert response_data["errorCode"] == ClientErrorCodes.ENTRY_NOT_FOUND

        assert (
            response_data["error"]
            == f"Entry '{entry_id}' not found in resource 'places' (version=latest)"
        )

    def test_update_wo_changes_succeeds(  # noqa: ANN201
        self,
        fa_data_client,
        write_token: auth.AccessToken,
    ):
        entry_id = 206
        entry_name = f"update{entry_id}"
        response = fa_data_client.put(
            "/entries/places",
            json={
                "entry": {
                    "code": entry_id,
                    "name": entry_name,
                    "population": 4,
                    "area": 50000,
                    "density": 5,
                    "municipality": [2, 3],
                }
            },
            headers=write_token.as_header(),
        )
        print(f"response = {response.json()}")
        entity_id = response.json()["newID"]
        assert response.status_code == status.HTTP_201_CREATED

        response = fa_data_client.post(
            f"/entries/places/{entity_id}",
            json={
                "entry": {
                    "code": entry_id,
                    "name": entry_name,
                    "population": 4,
                    "area": 50000,
                    "density": 5,
                    "municipality": [2, 3],
                },
                "message": "changes",
                "version": 1,
            },
            headers=write_token.as_header(),
        )
        assert response.status_code == status.HTTP_200_OK

    def test_update_wrong_version_fails(  # noqa: ANN201
        self,
        fa_data_client,
        write_token: auth.AccessToken,
    ):
        entry_id = 207
        response = fa_data_client.put(
            "/entries/places",
            json={
                "entry": {
                    "code": entry_id,
                    "name": "update3",
                    "population": 4,
                    "area": 50000,
                    "density": 5,
                    "municipality": [2, 3],
                }
            },
            headers=write_token.as_header(),
        )
        print(f"response = {response.json()}")
        entity_id = response.json()["newID"]

        assert response.status_code == 201

        response = fa_data_client.post(
            f"/entries/places/{entity_id}",
            json={
                "entry": {
                    "code": entry_id,
                    "name": "update3",
                    "population": 5,
                    "area": 50000,
                    "density": 5,
                    "municipality": [2, 3],
                },
                "message": "changes",
                "version": 2,
            },
            headers=write_token.as_header(),
            #         ),
            #         content_type='application/json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data["errorCode"] == ClientErrorCodes.VERSION_CONFLICT

        assert response_data["error"] == "Version conflict. Please update entry."
        assert response_data["diff"] == "Expecting version '1', got '2'"
        # TODO: should we return diff
        # assert response_data["diff"] == [
        #     {"type": "CHANGE", "field": "population", "before": 4, "after": 5}
        # ]

    def test_update_returns_200_on_valid_data(  # noqa: ANN201
        self,
        fa_data_client,
        write_token: auth.AccessToken,
    ):
        entry_id = 208
        entry_name = f"update{entry_id}"
        response = fa_data_client.put(
            "/entries/places",
            json={
                "entry": {
                    "code": entry_id,
                    "name": entry_name,
                    "population": 4,
                    "area": 50000,
                    "density": 5,
                    "municipality": [2, 3],
                }
            },
            headers=write_token.as_header(),
        )
        print(f"response = {response.json()}")
        entity_id = response.json()["newID"]

        assert response.status_code == status.HTTP_201_CREATED

        response = fa_data_client.post(
            f"/entries/places/{entity_id}",
            json={
                "entry": {
                    "code": entry_id,
                    "name": entry_name,
                    "population": 5,
                    "area": 50000,
                    "density": 5,
                    "municipality": [2, 3],
                },
                "message": "changes",
                "version": 1,
            },
            headers=write_token.as_header(),
        )
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["newID"] == entity_id

        entry_uow = get_entry_uow(
            fa_data_client.app.state.app_context.container, resource_id="places"
        )
        with entry_uow as uw:
            assert uw.repo.by_id(entity_id).body["population"] == 5
            assert entity_id in uw.repo.entity_ids()

    def test_update_several_times(  # noqa: ANN201
        self,
        fa_data_client,
        write_token: auth.AccessToken,
        entry_places_209_id: str,
    ):
        entry_id = 209

        entity_id = entry_places_209_id

        for i in range(2, 10):
            response = fa_data_client.post(
                f"/entries/places/{entity_id}",
                json={
                    "entry": {"code": entry_id, "name": "a" * i, "municipality": [1]},
                    "message": "changes",
                    "version": i - 1,
                },
                headers=write_token.as_header(),
            )
            print(f"i = {i}: response = {response.json()}")
            assert response.status_code == status.HTTP_200_OK

    @pytest.mark.xfail()
    def test_update_entry_id(  # noqa: ANN201
        self,
        fa_data_client,
        write_token: auth.AccessToken,
    ):
        entry_id = 210
        response = fa_data_client.put(
            "/entries/places",
            json={
                "entry": {
                    "code": entry_id,
                    "name": "update3",
                    "population": 4,
                    "area": 50000,
                    "density": 5,
                    "municipality": [2, 3],
                }
            },
            headers=write_token.as_header(),
        )
        assert response.status_code == 201

        response = fa_data_client.post(
            f"places/{entry_id}",
            json={
                "entry": {
                    "code": entry_id + 1,
                    "name": "update3",
                    "population": 5,
                    "area": 50000,
                    "density": 5,
                    "municipality": [2, 3],
                },
                "message": "changes",
                "version": 1,
            },
            headers=write_token.as_header(),
        )
        response_data = response.json()
        print(f"{response.json()=}")
        assert str(entry_id + 1) == response_data["newID"]

        entry_uow = get_entry_uow(
            fa_data_client.app.state.app_context.container, resource_id="places"
        )
        with entry_uow as uw:
            entry_ids = uw.repo.entry_ids()
            assert str(entry_id) not in entry_ids
            assert str(entry_id + 1) in entry_ids

    def test_update_changes_last_modified(  # noqa: ANN201
        self,
        fa_data_client,
        write_token: auth.AccessToken,
    ):
        entry_id = 212
        before_add = utc_now()

        ids = init(
            fa_data_client,
            [
                {"code": entry_id, "name": "last_modified1", "municipality": [1]},
            ],
            write_token,
        )

        after_add = utc_now()

        entry_uow = get_entry_uow(
            fa_data_client.app.state.app_context.container, resource_id="places"
        )
        entity_id = ids[0]
        with entry_uow as uw:
            entry = uw.repo.by_id(entity_id)
            assert entry.last_modified > before_add
            assert entry.last_modified < after_add

        fa_data_client.post(
            f"/entries/places/{entity_id}",
            json={
                "entry": {
                    "code": entry_id,
                    "name": "last_modified2",
                    "municipality": [1],
                },
                "message": "changes",
                "version": 1,
            },
            headers=write_token.as_header(),
        )

        after_update = utc_now()

        with entry_uow as uw:
            entry = uw.repo.by_id(entity_id)
            assert entry.last_modified > after_add
            assert entry.last_modified < after_update


class TestGetEntry:
    def test_get_entry_wo_auth_returns_403(  # noqa: ANN201
        self, fa_data_client, entry_places_214_id: str
    ):
        response = fa_data_client.get(f"/entries/places/{entry_places_214_id}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_entry_w_lower_auth_returns_403(  # noqa: ANN201
        self,
        fa_data_client,
        write_token: auth.AccessToken,
        entry_places_214_id: str,
    ):
        response = fa_data_client.get(
            f"/entries/places/{entry_places_214_id}",
            headers=write_token.as_header(),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_entry_by_entry_id(  # noqa: ANN201
        self,
        fa_data_client,
        admin_token: auth.AccessToken,
        entry_places_214_id: str,
    ):
        response = fa_data_client.get(
            f"/entries/places/{entry_places_214_id}",
            headers=admin_token.as_header(),
        )
        assert response.status_code == status.HTTP_200_OK

        entry = EntryDto(**response.json())
        assert entry.id == entry_places_214_id
        assert entry.version == 1

    def test_route_w_version_exist(  # noqa: ANN201
        self,
        fa_data_client,
        admin_token: auth.AccessToken,
        entry_places_209_id: str,
    ):
        response = fa_data_client.get(
            f"/entries/places/{entry_places_209_id}/5",
            headers=admin_token.as_header(),
        )
        assert response.status_code == status.HTTP_200_OK

        entry = EntryDto(**response.json())
        assert entry.id == entry_places_209_id
        assert entry.version == 5