import logging

try:
    from importlib.metadata import entry_points
except ImportError:
    from importlib_metadata import entry_points

from fastapi import FastAPI

logger = logging.getLogger("karp")

__version__ = "0.8.1"


def create_app() -> FastAPI:
    app = FastAPI(title="Karp TNG backend", redoc_url="/", version=__version__)
    # from .views import conf

    # conf.init_app(app)
    load_modules(app)
    return app


def load_modules(app=None):
    for ep in entry_points()["karp.modules"]:
        logger.info("Loading module: %s", ep.name)
        mod = ep.load()
        if app:
            init_app = getattr(mod, "init_app", None)
            if init_app:
                init_app(app)
