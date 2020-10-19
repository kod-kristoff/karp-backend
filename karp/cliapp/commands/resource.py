import logging
from pathlib import Path
from typing import Optional

import typer

from tabulate import tabulate

from karp.application.services import resources
from karp.errors import ResourceAlreadyPublished

from ..utility import cli_error_handler, cli_timer

logger = logging.getLogger("karp")


subapp = typer.Typer()


@subapp.command()
@cli_error_handler
@cli_timer
def create(config: Path):
    new_resources = []

    if config.is_file():
        with open(config) as fp:
            new_resource = resources.create_new_resource_from_file(fp)
        new_resources.append(new_resource)
    elif config.is_dir():
        typer.Abort()
        new_resources = resources.create_new_resource_from_dir(config)

    for resource_id in new_resources:
        typer.echo(f"Created resource {resource_id}")


@subapp.command()
@cli_error_handler
@cli_timer
def update(config: Path):
    if config.is_file():
        with open(config) as fp:
            new_resource = resources.update_resource_from_file(fp)
        new_resources = [new_resource]
    elif config.is_dir():
        new_resources = resources.update_resource_from_dir(config_dir)
    else:
        typer.echo("Must give either --config or --config-dir")
        raise typer.Exit(3)  # Usage error
    for (resource_id, version) in new_resources:
        if version is None:
            typer.echo(f"Nothing to do for resource '{resource_id}'")
        else:
            typer.echo(f"Updated version {version} of resource '{resource_id}'")


@subapp.command("import")
@cli_error_handler
@cli_timer
def import_resource(resource_id: str, version: Optional[int], data: Path):
    count = entries.add_entries_from_file(resource_id, version, data)
    typer.echo(f"Added {count} entries to {resource_id}, version {version}")


@subapp.command()
@cli_error_handler
@cli_timer
def publish(resource_id: str):
    try:
        resources.publish_resource(resource_id)
    except ResourceAlreadyPublished:
        typer.echo("Resource already published.")
    else:
        typer.echo(f"Resource '{resource_id}' is published ")


# @cli.command("reindex")
# @click.option("--resource_id", default=None, help="", required=True)
# @cli_error_handler
# @cli_timer
# def reindex_resource(resource_id):
#     try:
#         resource = resourcemgr.get_resource(resource_id)
#         indexmgr.publish_index(resource_id)
#         click.echo(
#             "Successfully reindexed all data in {resource_id}, version {version}".format(
#                 resource_id=resource_id, version=resource.version
#             )
#         )
#     except ResourceNotFoundError:
#         click.echo("No active version of {resource_id}".format(resource_id=resource_id))


# @cli.command("pre_process")
# @click.option("--resource_id", required=True)
# @click.option("--version", required=True)
# @click.option("--filename", required=True)
# @cli_error_handler
# @cli_timer
# def pre_process_resource(resource_id, version, filename):
#     resource = resourcemgr.get_resource(resource_id, version=version)
#     with open(filename, "wb") as fp:
#         processed = indexmgr.pre_process_resource(resource)
#         pickle.dump(processed, fp)


# @cli.command("publish_preprocessed")
# @click.option("--resource_id", required=True)
# @click.option("--version", required=True)
# @click.option("--data", required=True)
# @cli_error_handler
# @cli_timer
# def index_processed(resource_id, version, data):
#     with open(data, "rb") as fp:
#         try:
#             loaded_data = pickle.load(fp)
#             resourcemgr.publish_resource(resource_id, version)
#             indexmgr.reindex(resource_id, version=version, search_entries=loaded_data)
#         except EOFError:
#             click.echo("Something wrong with file")


# @cli.command("reindex_preprocessed")
# @click.option("--resource_id", required=True)
# @click.option("--data", required=True)
# @cli_error_handler
# @cli_timer
# def reindex_preprocessed(resource_id, data):
#     with open(data, "rb") as fp:
#         try:
#             loaded_data = pickle.load(fp)
#             indexmgr.reindex(resource_id, search_entries=loaded_data)
#         except EOFError:
#             click.echo("Something wrong with file")


@subapp.command("list")
@cli_error_handler
@cli_timer
def list_resources(
    show_active: Optional[bool] = typer.Option(True, "--show-active/--show-all")
):
    resources_ = resources.get_published_resources()
    if not resources_:
        typer.echo("No resources published.")
        raise typer.Exit()
    typer.echo(
        tabulate(
            [
                [resource.resource_id, resource.version, resource.is_published]
                for resource in resources_
            ],
            headers=["resource_id", "version", "published"],
        )
    )


# @cli.command("show")
# @click.option("--version", default=None, type=int)
# @click.argument("resource_id")
# @cli_error_handler
# @cli_timer
# def show_resource(resource_id, version):
#     if version:
#         resource = database.get_resource_definition(resource_id, version)
#     else:
#         resource = database.get_active_or_latest_resource_definition(resource_id)
#     if not resource:
#         click.echo(
#             "Can't find resource '{resource_id}', version '{version}'".format(
#                 resource_id=resource_id,
#                 version=version if version else "active or latest",
#             )
#         )
#         raise click.exceptions.Exit(3)

#     click.echo(
#         """
#     Resource: {resource.resource_id}
#     Version: {resource.version}
#     Active: {resource.active}
#     Config: {resource.config_file}
#     """.format(
#             resource=resource
#         )
#     )


# @cli.command("set_permissions")
# @click.option("--resource_id", required=True)
# @click.option("--version", required=True)
# @click.option("--level", required=True)
# @cli_error_handler
# @cli_timer
# def set_permissions(resource_id, version, level):
#     # TODO use level
#     permissions = {"write": True, "read": True}
#     resourcemgr.set_permissions(resource_id, version, permissions)
#     click.echo("updated permissions")


def export_resource():
    pass


def delete_resource():
    pass


def init_app(app):
    app.add_typer(subapp, name="resource")
