"""
Perform health checks on the server.

Used to perform readiness and liveness probes on the server.
"""

from dependency_injector import wiring
from fastapi import APIRouter, Response, status, Depends

from karp.application import schemas
from karp.main import AppContainer
from karp.services import system_monitor
from karp.services.auth_service import AuthService
from karp.services.messagebus import MessageBus


router = APIRouter()

# from .app_config import bus


@router.get("/healthz", response_model=schemas.SystemMonitorResponse)
@wiring.inject
def perform_health_check(
    response: Response,
    bus: MessageBus = Depends(wiring.Provide[AppContainer.bus]),
):
    print(f"bus = {bus!r}, type(bus) = {type(bus)}")
    # bus = bus()
    # print(f"bus = {bus!r}, type(bus) = {type(bus)}")

    db_status = system_monitor.check_database_status(bus.ctx)
    if not db_status:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    return {"database": db_status.message}


def init_app(app):
    app.include_router(router)
