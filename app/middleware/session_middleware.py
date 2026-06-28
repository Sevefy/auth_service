import logging
from abc import ABC, abstractmethod

from fastapi.requests import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.middleware.validate_session import ValidateTokenStrategy
from app.repository.postgres_session import SessionNotFoundError, TokenExpireError
from app.schemas.user import UserSession


logger = logging.getLogger(__name__)


class SecurityConfig:
    PRIVATE_PATHS = {
        "/api/v1/other/",
    }

    @staticmethod
    def is_private(path: str) -> bool:
        # Можно добавить более сложную логику
        return path in SecurityConfig.PRIVATE_PATHS or path.startswith("/private/") or path.startswith("/admin/")


class SessionMiddleware(BaseHTTPMiddleware):

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):

        if not SecurityConfig.is_private(request.url.path):
            return await call_next(request)

        logger.info("Проверка сессии")
        session_cookie = request.cookies.get("sessionToken")
        if session_cookie is None:
            raise Exception("Сессия не найдена в cookie")
        session_model = UserSession.model_validate_json(session_cookie)
        logger.info("Пользователь: %s", session_model.model_dump_json())
        # проверка существования сессии
        try:
            is_valid = await ValidateTokenStrategy(request, session_model).validate()
            if not is_valid:
                return JSONResponse(
                    content={
                        "detail": "Токен не валиден или не найден"
                    },
                    status_code=401
                )

        except (SessionNotFoundError, TokenExpireError) as exc:
            return JSONResponse(
                content={
                    "detail": str(exc)
                },
                status_code=401
            )

        response = await call_next(request)
        return response
