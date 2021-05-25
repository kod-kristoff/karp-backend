
from karp.domain.model import Resource
from karp.domain.commands import CreateResourceCommand
from karp.services import CreateResourceHandler
from karp.adapters.orm import SqlAlchemy
from karp.utility.unique_id import make_unique_id


def test_load_a_persisted_resource():

    db = SqlAlchemy('sqlite://')
    db.configure_mappings()
    db.recreate_schema()

    resource_id = make_unique_id()

    cmd = CreateResourceCommand(
        resource_id=resource_id,
        resource_short_name="lex",
        resource_name="Lex",
        last_modified_by="fred@example.org",
        config={"sort": "form"},
    )
    handler = CreateResourceHandler(db.unit_of_work_manager)
    handler.handle(cmd)

    resources = db.get_session().query(Resource).all()

    assert len(resources) == 1

    assert resources[0].description =='forgot my password again'

    assert resources[0].reporter.name == 'fred'

    assert resources[0].reporter.email == 'fred@example.org'
