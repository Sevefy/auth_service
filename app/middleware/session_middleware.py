import logging
from typing import Any

from fastapi.requests import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.middleware.validate_session import SessionValidationChain
from app.repository.postgres_session_repository import SessionNotFoundError, TokenExpireError

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

    def __init__(self, app) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Any:

        if not SecurityConfig.is_private(request.url.path):
            return await call_next(request)
        try:
            logger.info("Проверка сессии")
            session_cookie = request.cookies.get("sessionToken")
            if session_cookie is None:
                raise SessionNotFoundError("Сессия не найдена в куках")

            # проверка существования сессии
            user_session = await SessionValidationChain(request, session_cookie).validate()
            if user_session is None:
                raise TokenExpireError("Сессия не найдена или истекла")
            request.app.state.user_session = user_session
        except (SessionNotFoundError, TokenExpireError) as exc:
            response_fail = JSONResponse(
                content={
                    "detail": str(exc)
                },
                status_code=401
            )
            response_fail.delete_cookie("sessionToken")
            return response_fail

        response_next = await call_next(request)
        return response_next
