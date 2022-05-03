from typing import Callable
from fastapi import FastAPI

from karp.db_infrastructure import tasks as db_tasks
from karp.main import config

def create_start_app_handler(app: FastAPI) -> Callable:
    async def start_app() -> None:
        app.state.db = db_tasks.connect(config.DATABASE_URL)
    return start_app


def create_stop_app_handler(app: FastAPI) -> Callable:
    async def stop_app() -> None:
        db_tasks.close_db(app.state.db)
    return stop_app

