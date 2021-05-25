from .adapters import FakeUnitOfWork
from karp.services import CreateResourceHandler
from karp.domain.commands import CreateResourceCommand
from karp.utility.unique_id import make_unique_id


def test_creating_a_resource():
    user = "bob@example.org"
    name = "Lex"
    short_name = "lex"
    conf =
    resource_id = make_unique_id()
    uow = FakeUnitOfWork()

    handler = CreateResourceHandler(uow)
    cmd = CreateResourceCommand(
        resource_id=resource_id,
        name=name,
        short_name=short_name,
        last_modified_by=email,
    )

    handler.handle(cmd)

    assert uow.resources == 1

    assert uow.resources[0].reporter.name == name
    assert uow.resources[0].reporter.email == email

    assert uow.resources[0].description == desc

    assert uow.was_committed
