import pytest
from karp.adapters import repository
from karp.domain import model
from karp.utility.unique_id import make_unique_id

pytestmark = pytest.mark.usefixtures("mappers")


class TestResourceRepository:
    def test_get_by_id(self, sqlite_session_factory):
        session = sqlite_session_factory()
        repo = repository.SqlResourceRepository(session)
        resource_id1 = make_unique_id()
        r1 = model.Resource(
            resource_id=resource_id1,
            machine_name="res1",
            name="Res 1",
            last_modified_by="user",
            message="msg",
            config={},
        )
        repo.add(r1)
        assert repo.get(resource_id1) == r1
        assert repo.get(resource_id1).id == resource_id1
