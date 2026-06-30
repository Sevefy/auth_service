import logging

import asyncpg
from asyncpg import UniqueViolationError
from fastapi import APIRouter, Depends
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from redis import asyncio as redis

from app.config.cache import get_redis
from app.config.database import get_db_connection
from app.repository.postgres_session_repository import PostgresSessionRepository
from app.repository.redis_session_repository import RedisSessionRepository
from app.repository.user_repository import UserNotFoundError, UserRepository
from app.schemas.user import UserAuthSchema, UserSession, UserSessionCreateSchema
from app.utils.pwd_utils import PasswordNotValidError

logger = logging.getLogger(__name__)

user_router = APIRouter(prefix="/v1/users")


@user_router.post("/register")
async def register_user(
        user_data: UserAuthSchema,
        connection: asyncpg.Connection = Depends(get_db_connection)
) -> JSONResponse:
    try:
        user_id: int | None = await UserRepository.create_user(connection, user_data)
    except UniqueViolationError:
        return JSONResponse(
            content="Пользователь с таким именем уже существует",
            status_code=400
        )

    return JSONResponse(
        content=f"Пользователь создан: {user_id}",
        status_code=201
    )


@user_router.post("/auth")
async def auth_user(
        user_data: UserAuthSchema,
        connection: asyncpg.Connection = Depends(get_db_connection),
        redis_conn: redis.Redis = Depends(get_redis)
) -> JSONResponse:
    try:
        user: UserSessionCreateSchema = await UserRepository.auth_user(connection, user_data)
        user_session: UserSession | None = await PostgresSessionRepository.create_session(connection, user)

        if not isinstance(user_session, UserSession):
            raise ValueError("Сессия не может быть None")

    except (UserNotFoundError, PasswordNotValidError, ValueError) as exc:
        logger.error("Ошибка аутентификации: %s", exc)
        return JSONResponse(
            content={
                "error": exc.__class__.__name__,
                "message": str(exc)
            },
            status_code=400
        )

    await RedisSessionRepository.set_session(redis_conn, user_session)
    response = JSONResponse(
        content=f"Пользователь прошел аутентификацию: {repr(user_session)}",
        status_code=200
    )
    token = str(user_session.token)
    response.set_cookie(key="sessionToken", value=token, httponly=True)

    return response


@user_router.post("/logout")
async def logout(
        request: Request,
        connection: asyncpg.Connection = Depends(get_db_connection),
        redis_conn: redis.Redis = Depends(get_redis)
) -> JSONResponse:
    session_cookie = request.cookies.get("sessionToken")
    if session_cookie is None:
        return JSONResponse(content="Сессия не найдена", status_code=404)

    await PostgresSessionRepository.delete_session(connection, session_cookie)
    await RedisSessionRepository.delete_session(redis_conn, session_cookie)
    response = JSONResponse(
        content="Сессия закрыта",
        status_code=200
    )
    response.delete_cookie("sessionToken")
    return response
