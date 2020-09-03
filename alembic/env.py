from alembic import context
from sqlalchemy import engine_from_config, pool
from logging.config import fileConfig

from karp import models, config as karp_config
from karp.migration_helper import runtime_tables, history_tables


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)


def include_object(_object, name, type_, _reflected, _compare_to):
    return not (type_ == "table" and (name in runtime_tables or name in history_tables))


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    alembic_config = config.get_section(config.config_ini_section)
    alembic_config["sqlalchemy.url"] = karp_config.DB_URL

    connectable = engine_from_config(
        alembic_config, prefix="sqlalchemy.", poolclass=pool.NullPool
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=models.Base.metadata,
            include_object=include_object,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
