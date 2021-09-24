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





    @cli.group("resource")
    def resource():
        pass

    @resource.command("create")
    @click.option(
        "--config",
        default=None,
        help="A JSON file containing settings for one resource",
        required=False,
    )
    @click.option(
        "--config-dir",
        default=None,
        help="A directory containing config files for resource and optionally plugin settings",
        required=False,
    )
    @cli_error_handler
    @cli_timer
    def create_resource(config, config_dir):
        if config:
            with open(config) as fp:
                new_resource = resourcemgr.create_new_resource_from_file(fp)
            new_resources = [new_resource]
        elif config_dir:
            new_resources = resourcemgr.create_new_resource_from_dir(config_dir)
        else:
            click.echo("Must give either --config or --config-dir")
            raise click.exceptions.Exit(3)  # Usage error
        for (resource_id, version) in new_resources:
            click.echo(
                "Created version {version} of resource {resource_id}".format(
                    version=version, resource_id=resource_id
                )
            )

    @resource.command("update")
    @click.option(
        "--config",
        default=None,
        help="A JSON file containing settings for one resource",
        required=False,
    )
    @click.option(
        "--config-dir",
        default=None,
        help="A directory containing config files for resource and optionally plugin settings",
        required=False,
    )
    @cli_error_handler
    @cli_timer
    def update_resource(config, config_dir):
        if config:
            with open(config) as fp:
                new_resource = resourcemgr.update_resource_from_file(fp)
            new_resources = [new_resource]
        elif config_dir:
            new_resources = resourcemgr.update_resource_from_dir(config_dir)
        else:
            click.echo("Must give either --config or --config-dir")
            raise click.exceptions.Exit(3)  # Usage error
        for (resource_id, version) in new_resources:
            if version is None:
                click.echo(
                    "Nothing to do for resource '{resource_id}'".format(
                        resource_id=resource_id
                    )
                )
            else:
                click.echo(
                    "Updated version {version} of resource '{resource_id}'".format(
                        version=version, resource_id=resource_id
                    )
                )

    @resource.command("publish")
    @click.option("--resource_id", default=None, help="", required=True)
    @click.option("--version", default=None, help="", required=True)
    @cli_error_handler
    @cli_timer
    def publish_resource(resource_id, version):
        resource = resourcemgr.get_resource(resource_id, version=version)
        if resource.active:
            click.echo("Resource already published")
        else:
            indexmgr.publish_index(resource_id, version=version)
            click.echo(
                "Successfully indexed and published all data in {resource_id}, version {version}".format(
                    resource_id=resource_id, version=version
                )
            )

    @resource.command("reindex")
    @click.option("--resource_id", default=None, help="", required=True)
    @cli_error_handler
    @cli_timer
    def reindex_resource(resource_id):
        try:
            resource = resourcemgr.get_resource(resource_id)
            indexmgr.publish_index(resource_id)
            click.echo(
                "Successfully reindexed all data in {resource_id}, version {version}".format(
                    resource_id=resource_id, version=resource.version
                )
            )
        except ResourceNotFoundError:
            click.echo(
                "No active version of {resource_id}".format(resource_id=resource_id)
            )

    @resource.command("pre_process")
    @click.option("--resource_id", required=True)
    @click.option("--version", required=True)
    @click.option("--filename", required=True)
    @cli_error_handler
    @cli_timer
    def pre_process_resource(resource_id, version, filename):
        resource = resourcemgr.get_resource(resource_id, version=version)
        with open(filename, "wb") as fp:
            processed = indexmgr.pre_process_resource(resource)
            pickle.dump(processed, fp)

    @resource.command("publish_preprocessed")
    @click.option("--resource_id", required=True)
    @click.option("--version", required=True)
    @click.option("--data", required=True)
    @cli_error_handler
    @cli_timer
    def index_processed(resource_id, version, data):
        with open(data, "rb") as fp:
            try:
                loaded_data = pickle.load(fp)
                resourcemgr.publish_resource(resource_id, version)
                indexmgr.reindex(
                    resource_id, version=version, search_entries=loaded_data
                )
            except EOFError:
                click.echo("Something wrong with file")

    @resource.command("reindex_preprocessed")
    @click.option("--resource_id", required=True)
    @click.option("--data", required=True)
    @cli_error_handler
    @cli_timer
    def reindex_preprocessed(resource_id, data):
        with open(data, "rb") as fp:
            try:
                loaded_data = pickle.load(fp)
                indexmgr.reindex(resource_id, search_entries=loaded_data)
            except EOFError:
                click.echo("Something wrong with file")

    @resource.command("list")
    @click.option("--show-active/--show-all", default=False)
    @cli_error_handler
    @cli_timer
    def list_resources(show_active):
        if show_active:
            resources = resourcemgr.get_available_resources()
        else:
            resources = resourcemgr.get_all_resources()

        click.echo(tabulate(resources, headers=["resource_id", "version", "active"]))

    @resource.command("show")
    @click.option("--version", default=None, type=int)
    @click.argument("resource_id")
    @cli_error_handler
    @cli_timer
    def show_resource(resource_id, version):
        if version:
            resource = database.get_resource_definition(resource_id, version)
        else:
            resource = database.get_active_or_latest_resource_definition(resource_id)
        if not resource:
            click.echo(
                "Can't find resource '{resource_id}', version '{version}'".format(
                    resource_id=resource_id,
                    version=version if version else "active or latest",
                )
            )
            raise click.exceptions.Exit(3)

        click.echo(
            """
        Resource: {resource.resource_id}
        Version: {resource.version}
        Active: {resource.active}
        Config: {resource.config_file}
        """.format(
                resource=resource
            )
        )

    @resource.command("set_permissions")
    @click.option("--resource_id", required=True)
    @click.option("--version", required=True)
    @click.option("--level", required=True)
    @cli_error_handler
    @cli_timer
    def set_permissions(resource_id, version, level):
        # TODO use level
        permissions = {"write": True, "read": True}
        resourcemgr.set_permissions(resource_id, version, permissions)
        click.echo("updated permissions")

    def export_resource():
        pass

    def delete_resource():
        pass
