"""
Perform health checks on the server.

Used to perform readiness and liveness probes on the server.
"""

from fastapi import APIRouter, Response, status, Depends
from sqlalchemy.orm import Session

from karp import schemas
from karp.database import get_db
from karp.system_monitor import check_database_status

router = APIRouter()


@router.get("/healthz", response_model=schemas.SystemMonitorResponse)
def perform_health_check(response: Response, db: Session = Depends(get_db)):
    db_status = check_database_status(db)
    if not db_status:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    return {"database": db_status.message}


def init_app(app):
    app.include_router(router, tags=["system monitor"])
