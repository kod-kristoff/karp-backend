import os
import logging
from distutils.util import strtobool
from typing import Optional

import pydantic
from sqlalchemy.engine import url as sa_url


MYSQL_FORMAT = "mysql://{user}:{passwd}@{dbhost}/{dbname}"


class Config(pydantic.BaseSettings):
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    DEBUG: bool = False
    TESTING: bool = False
    DB_DRIVER: str = "mysql+pymysql"
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    DB_HOST: Optional[str] = None
    DB_PORT: Optional[int] = None
    DB_DATABASE: Optional[str] = None
    SQLALCHEMY_DATABASE_URI: sa_url.URL
    ELASTICSEARCH_HOST: list = []
    ELASTICSEARCH_ENABLED: bool = False
    # CONSOLE_LOG_LEVEL = logging.getLevelName(
    #     os.environ.get("CONSOLE_LOG_LEVEL", "INFO")
    # )
    CONSOLE_LOG_LEVEL = logging.INFO
    LOG_TO_SLACK: bool = False
    SLACK_SECRET: str = os.environ.get("SLACK_SECRET")
    JWT_AUTH: bool = False
    REVERSE_PROXY_PATH: Optional[str] = None

    @pydantic.validator("SQLALCHEMY_DATABASE_URI", pre=True, always=True)
    def build_db_url(cls, v, *, values, **kwargs):
        if v:
            db_url = sa_url.make_url(v)
        else:
            db_url = sa_url.URL(
                drivername=values["DB_DRIVER"],
                username=values["DB_USER"],
                password=values["DB_PASSWORD"],
                host=values["DB_HOST"],
                port=values["DB_PORT"],
                database=values["DB_DATABASE"],
            )
        return db_url


class ProductionConfig(Config):
    def __init__(self):
        self.SQLALCHEMY_DATABASE_URI = MYSQL_FORMAT.format(
            user=os.environ["MARIADB_USER"],
            pwd=os.environ["MARIADB_PASSWORD"],
            dbhost=os.environ["MARIADB_HOST"],
            dbname=os.environ["MARIADB_DATABASE"],
        )


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True


def get_config():
    return Config()


class MariaDBConfig(Config):
    def __init__(
        self, user=None, pwd=None, host=None, dbname=None, setup_database=False
    ):
        if not user:
            user = os.environ["MARIADB_USER"]
        if not pwd:
            pwd = os.environ["MARIADB_PASSWORD"]
        if not host:
            host = os.environ["MARIADB_HOST"]
        if not dbname:
            dbname = os.environ["MARIADB_DATABASE"]

        self.SETUP_DATABASE = setup_database
        self.SQLALCHEMY_DATABASE_URI = MYSQL_FORMAT.format(
            user=user, passwd=pwd, dbhost=host, dbname=dbname
        )
