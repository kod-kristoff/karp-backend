"""Pytest entry point."""
import pytest

from starlette.config import environ

environ["TESTING"] = "True"
environ["ELASTICSEARCH_HOST"] = "localhost:9202"
environ["CONSOLE_LOG_LEVEL"] = "DEBUG"

from karp.tests import common_data, utils  # nopep8  # noqa: E402, F401


@pytest.fixture
def json_schema_config():
    return common_data.CONFIG_PLACES