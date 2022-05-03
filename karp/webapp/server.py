from fastapi import FastAPI

from starlette.middleware.cors import CORSMiddleware

from karp.webapp import tasks
from karp.webapp.routes import router as api_router

def create_application() -> FastAPI:
    app = FastAPI(title="KARP backend", version="6.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_event_handler("startup", tasks.create_start_app_handler(app))
    app.add_event_handler("shutdown", tasks.create_stop_app_handler(app))

    app.include_router(api_router)

    return app


app = create_application()
