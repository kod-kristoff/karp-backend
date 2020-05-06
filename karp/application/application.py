"""Application."""
import logging

import attr

from karp.application.config import Config
from karp.application.context import Context


@attr.s(auto_attribs=True)
class Application:
    config: Config = attr.Factory(Config)
    context: Context = attr.Factory(Context)


def create_application() -> Application:
    return Application()
