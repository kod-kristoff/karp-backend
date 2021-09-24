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


_logger = logging.getLogger("karp")


def create_app():

    from karp import create_app

    return create_app(MariaDBConfig())


def create_cliapp():
    @click.group(cls=FlaskGroup, create_app=create_app)
    def cli():
        pass

    def cli_error_handler(func):
        def func_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except KarpError as e:
                _logger.error(e.message)
                raise click.exceptions.Exit(e.code)

        return func_wrapper

    def cli_timer(func):
        def func_wrapper(*args, **kwargs):
            before_t = time.time()
            result = func(*args, **kwargs)
            click.echo("Command took: %0.1fs" % (time.time() - before_t))
            return result

        return func_wrapper


    load_commands(cli)

    return cli


def load_commands(app=None):
    if not entry_points().get("karp.clicommands"):
        print("No cli modules to load.")
        return
    for ep in entry_points()["karp.clicommands"]:
        _logger.info("Loading cli module: %s", ep.name)
        print("Loading cli module: %s" % ep.name)
        mod = ep.load()
        if app:
            init_app = getattr(mod, "init_app", None)
            if init_app:
                init_app(app)


cli = create_cliapp()
