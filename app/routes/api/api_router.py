from fastapi import APIRouter

from app.routes.api.v1.other import other_router
from app.routes.api.v1.user import user_router

api_router = APIRouter(prefix="/api")

api_router.include_router(user_router)
api_router.include_router(other_router)