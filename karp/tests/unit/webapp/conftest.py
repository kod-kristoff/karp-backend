from httpx import Client
from fastapi import FastAPI
import pytest

from karp.main import AppContext
from karp.webapp.main import create_app
from karp.tests.unit.lex.conftest import lex_ctx


@pytest.fixture()
def app_context(lex_ctx) -> AppContext:
    return AppContext(lex_ctx, {})


@pytest.fixture()
def app(app_context: AppContext) -> FastAPI:
    return create_app(app_context)


@pytest.fixture()
def client(app: FastAPI) -> Client:
    with Client(
        app=app,
        base_url="http://testserver",
    ) as client:
        yield client

