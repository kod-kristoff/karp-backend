import os
import pkg_resources
import json
import logging
from flask import Flask     # pyre-ignore
from flask_cors import CORS  # pyre-ignore

from karp.errors import KarpError
import karp.util.logging.slack as slack_logging

__version__ = '0.6.4'


# TODO handle settings correctly
def create_app(config_class=None):
    app = Flask(__name__)
    app.config.from_object('karp.config.DevelopmentConfig')
    if config_class:
        app.config.from_object(config_class)
    if os.getenv('KARP_CONFIG'):
        app.config.from_object(os.getenv('KARP_CONFIG'))

    logger = setup_logging(app)

    from .api import health_api, edit_api, query_api, conf_api, documentation, stats_api
    app.register_blueprint(edit_api)
    app.register_blueprint(health_api)
    app.register_blueprint(query_api)
    app.register_blueprint(conf_api)
    app.register_blueprint(documentation)
    app.register_blueprint(stats_api)

    from .init import init_db
    init_db(app)

    if app.config['ELASTICSEARCH_ENABLED'] and app.config.get('ELASTICSEARCH_HOST', ''):
        from karp.elasticsearch import init_es
        init_es(app.config['ELASTICSEARCH_HOST'])
    else:
        # TODO if an elasticsearch test runs before a non elasticsearch test this
        # is needed to reset the index and search modules
        from karp.search import SearchInterface, search
        from karp.indexmgr.index import IndexInterface
        from karp.indexmgr import indexer
        search.init(SearchInterface())
        indexer.init(IndexInterface())

    @app.errorhandler(Exception)
    def http_error_handler(error: Exception):
        if isinstance(error, KarpError):
            logger.debug(error.message)
            return json.dumps({'error': error.message}), 400
        else:
            logger.exception('unhandled exception')
            return json.dumps({'error': 'unknown error'}), 400

    import karp.auth.auth as auth
    if app.config['JWT_AUTH']:
        from karp.auth.jwt_authenticator import JWTAuthenticator
        auth.auth.set_authenticator(JWTAuthenticator())
    else:
        from karp.auth.authenticator import Authenticator
        auth.auth.set_authenticator(Authenticator())

    CORS(app)

    return app


def setup_logging(app):
    logger = logging.getLogger('karp')
    if app.config.get('LOG_TO_SLACK'):
        slack_handler = slack_logging.get_slack_logging_handler(app.config.get('SLACK_SECRET'))
        logger.addHandler(slack_handler)
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.setLevel(app.config['CONSOLE_LOG_LEVEL'])
    logger.addHandler(console_handler)
    return logger


def get_version() -> str:
    return __version__


def get_resource_string(name: str) -> str:
    return pkg_resources.resource_string(__name__, name).decode('utf-8')
