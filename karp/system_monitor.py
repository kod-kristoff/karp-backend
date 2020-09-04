"""System monitor."""
import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from karp import schemas

logger = logging.getLogger("karp")


def check_database_status(db: Session) -> schemas.SystemResponse:
    """Check database status.

    Args:
        db (Session): the session to use

    Returns:
        schemas.SystemResponse: the response
    """
    try:
        # to check database we will execute raw query
        db.execute("SELECT 1")
        return schemas.SystemOk()
    except SQLAlchemyError as e:
        logger.exception(e)
        return schemas.SystemNotOk(message=str(e))
