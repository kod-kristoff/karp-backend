import json
from typing import Any, Optional, Tuple
from httpx import AsyncClient

from starlette.testclient import TestClient
from typer import Option

from karp import auth
from karp.webapp import schemas


class KarpClientBase:
    def make_resource_create(self, path_to_config: str) -> schemas.ResourceCreate:
        with open(path_to_config) as fp:
            resource_config = json.load(fp)

        resource_id = resource_config.pop("resource_id")
        return schemas.ResourceCreate(
            resource_id=resource_id,
            name=resource_config.pop("resource_name"),
            config=resource_config,
            message=f"{resource_id} added",
        )


class KarpClient(KarpClientBase):
    def __init__(self, client: TestClient):
        self.client = client

    def create_and_publish_resource(
        self,
        *,
        path_to_config: str,
        access_token: auth.AccessToken,
    ) -> Tuple[bool, Optional[dict[str, Any]]]:

        resource = self.make_resource_create(path_to_config)
        resource_exists = self.client.get(
            f"/resources/{resource.resource_id}", headers=access_token.as_header()
        )
        if resource_exists.status_code == 200:
            return True, None
        response = self.client.post(
            "/resources/",
            json=resource.dict(),
            headers=access_token.as_header(),
        )
        if response.status_code != 201:
            return False, {
                "error": f"Failed create resource: unexpected status_code: {response.status_code} != 201 ",
                "response.json": response.json(),
            }

        response = self.client.post(
            f"/resources/{resource.resource_id}/publish",
            json={
                "message": f"{resource.resource_id} published",
            },
            headers=access_token.as_header(),
        )
        if response.status_code != 200:
            return False, {
                "error": f"Failed publish resource: unexpected status_code: {response.status_code} != 200 ",
                "response.json": response.json(),
            }

        return True, None

    def add_entries(
        self,
        entries: dict,
        access_token: auth.AccessToken,
    ) -> Tuple[bool, Optional[dict[str, Any]]]:
        for resource, res_entries in entries.items():
            for entry in res_entries:
                response = self.client.post(
                    f"/entries/{resource}/add",
                    json={"entry": entry},
                    headers=access_token.as_header(),
                )
                if response.status_code != 201:
                    return False, {
                        "message": f"Failed add entry: unexpected status_code: {response.status_code} != 201",
                        "entry": entry,
                        "response.json": response.json(),
                    }
        return True, None


class AsyncKarpClient(KarpClientBase):
    def __init__(self, client: AsyncClient):
        self.client = client

    async def create_and_publish_resource(
        self, *, path_to_config: str, access_token: auth.AccessToken
    ) -> Tuple[bool, Optional[dict[str, Any]]]:
        resource = self.make_resource_create(path_to_config)
        resource_exists = await self.client.get(
            f"/resources/{resource.resource_id}", headers=access_token.as_header()
        )
        if resource_exists.status_code == 200:
            return True, None
        response = await self.client.post(
            "/resources/",
            json=resource.dict(),
            headers=access_token.as_header(),
        )
        if response.status_code != 201:
            return False, {
                "error": f"Failed create resource: unexpected status_code: {response.status_code} != 201 ",
                "response.json": response.json(),
            }

        response = await self.client.post(
            f"/resources/{resource.resource_id}/publish",
            json={
                "message": f"{resource.resource_id} published",
            },
            headers=access_token.as_header(),
        )
        if response.status_code != 200:
            return False, {
                "error": f"Failed publish resource: unexpected status_code: {response.status_code} != 200 ",
                "response.json": response.json(),
            }

        return True, None

    async def add_entries(
        self,
        entries: dict,
        access_token: auth.AccessToken,
    ) -> Tuple[bool, Optional[dict[str, Any]]]:
        for resource, res_entries in entries.items():
            for entry in res_entries:
                response = await self.client.post(
                    f"/entries/{resource}/add",
                    json={"entry": entry},
                    headers=access_token.as_header(),
                )
                if response.status_code != 201:
                    return False, {
                        "message": f"Failed add entry: unexpected status_code: {response.status_code} != 201",
                        "entry": entry,
                        "response.json": response.json(),
                    }
        return True, None
