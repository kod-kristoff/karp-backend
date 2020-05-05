import logging

from karp.application.application import create_application, Application


def test_create_application_creates_application():
    app = create_application()

    assert isinstance(app, Application)
