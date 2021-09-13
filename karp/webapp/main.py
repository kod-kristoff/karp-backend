import traceback
import logging

try:
    from importlib.metadata import entry_points
except ImportError:
    # used if python < 3.8
    from importlib_metadata import entry_points  # type: ignore

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from karp import main

from karp.main.containers import AppContainer
from . import app_config


__version__ = "0.8.1"


def create_app(*, with_context: bool = True) -> FastAPI:
    app = FastAPI(title="Karp API", redoc_url="/", version=__version__)
    app_context = main.bootstrap_app()

    from karp.application.logger import setup_logging

    logger = setup_logging()

    # if with_context:
    #     from karp.application.services.contexts import init_context

    #     init_context()
    # container = AppContainer(context=app_context.container)

    # container.config.auth.jwt.pubkey_path.from_env("JWT_AUTH_PUBKEY_PATH")

    from . import entries_api
    from . import health_api
    from . import history_api
    from . import query_api
    from . import resources_api
    from . import stats_api

    app_context.container.wire(
        modules=[
            app_config,
            entries_api,
            health_api,
            history_api,
            query_api,
            resources_api,
            stats_api,
        ]
    )

    entries_api.init_app(app)
    health_api.init_app(app)
    history_api.init_app(app)
    query_api.init_app(app)
    resources_api.init_app(app)
    stats_api.init_app(app)

    app.container = app_context.container

    load_modules(app)

    from karp.errors import KarpError

    @app.exception_handler(KarpError)
    async def _karp_error_handler(request: Request, exc: KarpError):
        logger.exception(exc)
        traceback.print_exception(KarpError, exc, None)
        return JSONResponse(
            status_code=exc.http_return_code,
            content={"error": exc.message, "errorCode": exc.code},
        )

    return app


def load_modules(app=None):
    logger = logging.getLogger("karp")

    if "karp.modules" in entry_points():
        for ep in entry_points()["karp.modules"]:
            logger.info("Loading module: %s", ep.name)
            print("Loading module: %s" % ep.name)
            mod = ep.load()
            if app:
                init_app = getattr(mod, "init_app", None)
                if init_app:
                    init_app(app)
