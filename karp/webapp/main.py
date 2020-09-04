import logging

try:
    from importlib.metadata import entry_points
except ImportError:
    from importlib_metadata import entry_points

from fastapi import FastAPI


__version__ = "0.8.1"


def create_app() -> FastAPI:
    app = FastAPI(title="Karp API", redoc_url="/", version=__version__)
    logger = setup_logging(app)
    load_modules(logger, app)
    print(f"app = {app.routes!r}")
    return app


def load_modules(logger, app=None):
    logger.info("load_modules called")
    logger.info("entry_points: %s", set(entry_points()["karp.modules"]))
    for ep in set(entry_points()["karp.modules"]):
        logger.info("Loading module: %s", ep.name)
        mod = ep.load()
        if app:
            init_app = getattr(mod, "init_app", None)
            if init_app:
                logger.info("Initailizing module: %s", ep.name)
                init_app(app)


def setup_logging(app):
    logger = logging.getLogger("karp")
    from karp import config

    if config.LOG_TO_SLACK:
        from karp.utility import slack_logging

        slack_handler = slack_logging.get_slack_logging_handler(config.SLACK_SECRET)
        logger.addHandler(slack_handler)
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    logger.setLevel(config.LOG_LEVEL)
    logger.addHandler(console_handler)
    return logger
