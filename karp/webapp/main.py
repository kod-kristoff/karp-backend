import traceback
import logging

try:
    from importlib.metadata import entry_points
except ImportError:
    from importlib_metadata import entry_points

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


__version__ = "0.8.1"


def create_app() -> FastAPI:
    app = FastAPI(title="Karp API", redoc_url="/", version=__version__)

    from karp.application.logger import setup_logging

    logger = setup_logging()

    from karp.application.services.contexts import init_context

    init_context()

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

    for ep in entry_points()["karp.modules"]:
        logger.info("Loading module: %s", ep.name)
        print("Loading module: %s" % ep.name)
        mod = ep.load()
        if app:
            init_app = getattr(mod, "init_app", None)
            if init_app:
                init_app(app)
