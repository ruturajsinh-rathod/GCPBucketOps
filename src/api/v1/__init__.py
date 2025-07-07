from fastapi import APIRouter

from src.api.v1.file.controllers import user_router

router = APIRouter(prefix="/api/v1")

# Attach child routers to main router
router.include_router(user_router)

__all__ = ["router"]
