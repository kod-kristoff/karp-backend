import os
import pkg_resources
import json
import logging
from flask import Flask  # pyre-ignore
from flask_cors import CORS  # pyre-ignore
from flask import request  # pyre-ignore
import flask_reverse_proxy
import werkzeug.exceptions

# from karp import application
from karp.errors import KarpError
import karp.util.logging.slack as slack_logging

__version__ = "0.8.1"


# TODO handle settings correctly
def create_app(config_class=None):
    app = Flask(__name__)
    app.config.from_object("karp.application.config.DevelopmentConfig")
    if config_class:
        app.config.from_object(config_class)
    if os.getenv("KARP_CONFIG"):
        app.config.from_object(os.getenv("KARP_CONFIG"))

    logger = setup_logging(app)

    from karp import application
    from karp.infrastructure.sql.resource_repository import SqlResourceRepository

    application.ctx.resource_repo = SqlResourceRepository(
        config_class.SQLALCHEMY_DATABASE_URI
    )

    from karp.infrastructure.sql import db

    db.set_default_uri(config_class.SQLALCHEMY_DATABASE_URI)

    if app.config.get("SETUP_DATABASE", True):
        from .resourcemgr import setup_resource_classes

        with app.app_context():
            setup_resource_classes()

    if app.config["ELASTICSEARCH_ENABLED"] and app.config.get("ELASTICSEARCH_HOST", ""):
        from karp.infrastructure.elasticsearch6 import init_es

        index_service, search_service = init_es(app.config["ELASTICSEARCH_HOST"])
        application.ctx.index_service = index_service
        application.ctx.search_service = search_service
    else:
        # TODO if an elasticsearch test runs before a non elasticsearch test this
        # is needed to reset the index and search modules
        from karp import search
        from karp.domain.services.indexmgr.index import IndexService
        from karp.domain.services.indexmgr import indexer

        search.init(search.SearchService())
        indexer.init(IndexService())
        application.ctx.index_service = IndexService()
        application.ctx.search_service = search.SearchService()

    with app.app_context():
        import karp.pluginmanager

        karp.pluginmanager.init()

    from karp.domain.services.auth import auth

    application.ctx.auth_service = auth.Auth()
    if app.config["JWT_AUTH"]:
        from karp.domain.services.auth.jwt_authenticator import JWTAuthenticator

        application.ctx.auth_service.set_authenticator(JWTAuthenticator())
    else:
        from karp.domain.services.auth.authenticator import Authenticator

        application.ctx.auth_service.set_authenticator(Authenticator())

    from .api import (
        health_api,
        edit_api,
        query_api,
        conf_api,
        documentation,
        stats_api,
        history_api,
    )

    app.register_blueprint(edit_api)
    app.register_blueprint(health_api)
    app.register_blueprint(query_api)
    app.register_blueprint(conf_api)
    app.register_blueprint(documentation)
    app.register_blueprint(stats_api)
    app.register_blueprint(history_api)

    @app.errorhandler(Exception)
    def http_error_handler(error: Exception):
        error_str = "Exception on %s [%s]" % (request.path, request.method)
        if isinstance(error, werkzeug.exceptions.NotFound):
            logger.debug(error_str)
            return "", 404

        if isinstance(error, KarpError):
            logger.debug(error_str)
            logger.debug(error.message)
            error_code = error.code if error.code else 0
            return (
                json.dumps({"error": error.message, "errorCode": error_code}),
                error.http_return_code,
            )
        else:
            if app.config["DEBUG"]:
                raise error
            logger.error(error_str)
            logger.exception("unhandled exception")
            return json.dumps({"error": "unknown error", "errorCode": 0}), 400

    CORS(app)

    app.wsgi_app = flask_reverse_proxy.ReverseProxied(app.wsgi_app)
    return app


def setup_logging(app):
    logger = logging.getLogger("karp")
    if app.config.get("LOG_TO_SLACK"):
        slack_handler = slack_logging.get_slack_logging_handler(
            app.config.get("SLACK_SECRET")
        )
        logger.addHandler(slack_handler)
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    logger.setLevel(app.config["CONSOLE_LOG_LEVEL"])
    logger.addHandler(console_handler)
    return logger


def get_version() -> str:
    return __version__


def get_resource_string(name: str) -> str:
    return pkg_resources.resource_string(__name__, name).decode("utf-8")
