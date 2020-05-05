"""Application."""
import logging

import attr


@attr.s(auto_attribs=True)
class ApplicationConfig:
    LOG_TO_SLACK: bool = False
    SLACK_SECRET: str = None
    CONSOLE_LOG_LEVEL: int = logging.DEBUG



class Application:
    pass


def create_application() -> Application:
    return Application()
