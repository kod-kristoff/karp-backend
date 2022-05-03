import logging
import os
import databases import Database

from karp.main.config import DATABASE_URL


logger = logging.getLogger(__name__)

async def connect_to_db() -> Database:
    if DATABASE_URL.scheme.startswith('sqlite'):
        database = Database(DATABASE_URL)
    else:
        database = Database(DATABASE_URL, min_size=2, max_size=10)
    try:
        await database.connect()
        return database
    except Exception as e:
        logger.warn("--- DB CONNECTION ERROR ---")
        logger.warn(e)
        logger.warn("--- DB CONNECTION ERROR ---")


async def close_db_connection(database: Database) -> None:
    try:
        await database.disconnect()
    except Exception as e:
        logger.warn("--- DB DISCONNECT ERROR ---")
        logger.warn(e)
        logger.warn("--- DB DISCONNECT ERROR ---")

