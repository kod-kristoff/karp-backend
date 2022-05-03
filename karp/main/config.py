import os

import environs
from sqlalchemy.engine import url as sa_url
from databases import DatabaseURL
from starlette.config import Config
from starlette.datastructures import Secret

PROJECT_NAME = "phresh"
VERSION = "1.0.0"
API_PREFIX = "/"
# SECRET_KEY = config("SECRET_KEY", cast=Secret, default="CHANGEME")



def load_env() -> environs.Env:
    config_path = os.environ.get("CONFIG_PATH", ".env")
    print(f"loading config from '{config_path}'")
    env = environs.Env()
    env.read_env(config_path)
    return env


def parse_database_name(env: environs.Env) -> str:
    database_name = env('DB_DATABASE', 'karp')
    if env('TESTING', None):
        database_name = env('DB_TEST_DATABASE',
                            None) or f'{database_name}_test'
    return database_name


def parse_database_url(env: environs.Env) -> DatabaseURL:
    database_url = env('DATABASE_URL', None)
    if env.bool('TESTING', False):
        database_test_url = env('DATABASE_TEST_URL', None)
        if database_test_url:
            return DatabaseURL(database_test_url)
        elif database_url:
            return DatabaseURL(f'{database_url}_test')

    if database_url:
        return DatabaseURL(database_url)

    database_name = parse_database_name(env)

    database_url = '{driver}://{user}:{password}@{host}:{port}/{database}'.format(
        driver=env('DB_DRIVER', 'mysql'),
        user=env('DB_USER'),
        password=env('DB_PASSWORD'),
        host=env('DB_HOST'),
        port=env.int('DB_PORT', 3306),
        database=database_name,
    )
    return DatabaseURL(database_url)


config = load_env()


DATABASE_URL = parse_database_url(config)
DATABASE_NAME = parse_database_name(config)


def parse_sqlalchemy_url(env: environs.Env) -> sa_url.URL:
    db_url = env('DB_URL', None)
    if db_url:
        return sa_url.make_url(db_url)
    database = parse_sqlalchemy_database_name(env)
    return sa_url.URL.create(
        drivername=env('DB_DRIVER', 'mysql+pymysql'),
        username=env('DB_USER', None),
        password=env('DB_PASSWORD', None),
        host=env('DB_HOST', None),
        port=env.int('DB_PORT', None),
        database=database,
        query={'charset': 'utf8mb4'}
    )


def parse_sqlalchemy_database_name(env: environs.Env) -> str:
    database_name = env('DB_DATABASE', None)
    if env('TESTING', None):
        database_name = env('DB_TEST_DATABASE',
                            None) or f'{database_name}_test'
    return database_name


def parse_sqlalchemy_url_wo_db(env: environs.Env) -> sa_url.URL:
    return sa_url.URL.create(
        drivername=env('DB_DRIVER', 'mysql+pymysql'),
        username=env('DB_USER', None),
        password=env('DB_PASSWORD', None),
        host=env('DB_HOST', None),
        port=env.int('DB_PORT', None),
        database='',
        query={'charset': 'utf8mb4'}
    )
