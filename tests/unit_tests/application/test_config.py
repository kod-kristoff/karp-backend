import logging

from karp.application.config import Config


def test_config_w_defaults():
    app_config = Config()

    assert not app_config.LOG_TO_SLACK
    assert app_config.SLACK_SECRET is None
    assert app_config.CONSOLE_LOG_LEVEL == logging.INFO
    assert not app_config.SQLALCHEMY_TRACK_MODIFICATIONS
    assert not app_config.DEBUG
    assert not app_config.TESTING
    assert app_config.SQLALCHEMY_DATABASE_URI == "sqlite:///:memory:"
    assert app_config.ELASTICSEARCH_HOST is None
    assert not app_config.ELASTICSEARCH_ENABLED
    assert not app_config.JWT_AUTH
