import logging
from typing import List, Tuple

from karp import models
from karp.database import SessionLocal


logger = logging.getLogger("karp")


def find_tables() -> Tuple[List[str], List[str]]:
    db = SessionLocal()
    entry_tables = []
    history_tables = []
    try:
        for resource in db.query(models.ResourceDefinition).all():
            entry_table_name = f"{resource.resource_id}_{resource.version}"
            entry_tables.append(entry_table_name)
            history_tables.append(entry_table_name + "_history")
        return entry_tables, history_tables
    except Exception as e:
        logger.exception(e)
        return [], []


entry_tables, history_tables = find_tables()
