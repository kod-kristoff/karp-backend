from fastapi import APIRouter

from karp.webapp.routes import (
    entries_api,
    resources_api,
)


router = APIRouter()


router.include_router(
    entries_api.new_router,
    prefix='/entries',
    tags=['entries']
)
router.include_router(resources_api.new_router, tags=['resources'])
