from fastapi import APIRouter

from app.routes.api.api_router import api_router

router = APIRouter(prefix="", tags=["router"])

router.include_router(api_router)