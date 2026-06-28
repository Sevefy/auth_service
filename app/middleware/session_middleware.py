import logging

from fastapi.requests import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.middleware.validate_session import SessionValidationChain
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
        try:
            logger.info("Проверка сессии")
            session_cookie = request.cookies.get("sessionToken")
            if session_cookie is None:
                raise SessionNotFoundError("Сессия не найдена в куках")

            session_model = UserSession.model_validate_json(session_cookie)
            logger.info("Пользователь: %s", session_model.model_dump_json())
            # проверка существования сессии

            is_valid = await SessionValidationChain(request, session_model).validate()
            if not is_valid:
                raise TokenExpireError("Сессия не найдена или истекла")

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
