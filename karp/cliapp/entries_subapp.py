import logging
import time
import click
import pickle
from pathlib import Path

try:
    from importlib.metadata import entry_points
except ImportError:
    from importlib_metadata import entry_points

from flask.cli import FlaskGroup  # pyre-ignore
import json_streams
from tabulate import tabulate
import dotenv

dotenv.load_dotenv(".env", verbose=True)

from .config import MariaDBConfig
from karp import resourcemgr
from karp.resourcemgr import entrywrite
from karp import indexmgr
from karp import database
from karp.errors import KarpError, ResourceNotFoundError


    # Entries commands

    @cli.group("entries")
    def entries():
        pass

    @entries.command("import")
    @click.option("--resource_id", default=None, help="", required=True)
    @click.option("--version", default=None, help="", required=True)
    @click.option("--data", default=None, help="", required=True)
    @cli_error_handler
    @cli_timer
    def import_resource(resource_id, version, data):
        entry_ids = entrywrite.add_entries_from_file(resource_id, version, data)
        click.echo(
            f"Added {len(entry_ids)} entries to {resource_id}, version {version}"
        )

    @entries.command("update")
    @click.option("--resource_id", default=None, help="", required=True)
    @click.option("--version", default=None, help="", required=False, type=int)
    @click.option("--data", default=None, help="", required=True)
    @cli_error_handler
    @cli_timer
    def update_entries(resource_id, version, data):
        result = entrywrite.update_entries(
            resource_id=resource_id,
            entries=json_streams.load_from_file(data),
            user_id="local admin",
            message="update by admin",
            resource_version=version,
        )

        if result["failure"]:
            click.echo(f"{len(result['success'])} entries were successfully updated.")
            click.echo(f"There were {len(result['failure'])} errors:")
            click.echo(tabulate(result["failure"]))
        else:
            click.echo(
                f"All {len(result['success'])} entries were successfully updated."
            )

    @entries.command("delete")
    @click.option(
        "--resource_id",
        default=None,
        help="The resource to delete entries from",
        required=True,
    )
    # @click.option("--version", default=None, help="", required=False, type=int)
    @click.option("--data", default=None, help="", required=True)
    @cli_error_handler
    @cli_timer
    def delete_entries(resource_id: str, data: Path):
        result = entrywrite.delete_entries(
            resource_id=resource_id,
            entry_ids=json_streams.load_from_file(data),
            user_id="local admin",
            # resource_version=version,
        )

        if result["failure"]:
            click.echo(f"{len(result['success'])} entries were successfully deleted.")
            click.echo(f"There were {len(result['failure'])} errors:")
            click.echo(tabulate(result["failure"]))
        else:
            click.echo(
                f"All {len(result['success'])} entries were successfully deleted."
            )

