from karp.application.context import Context
from karp.application.services.system_monitor import check_database_status


def test_system_monitor_without_setup():
    context = Context()

    response = check_database_status(context)

    assert not response
    assert response.message == "No resource_repository is configured."
