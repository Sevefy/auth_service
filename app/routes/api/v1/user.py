import logging

import asyncpg
from fastapi import APIRouter, Depends
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from app.config.cache import get_redis
from app.config.database import get_db_connection
from app.repository.redis_session import RedisSessionRepository
from app.repository.postgres_session import PostgresSessionRepository
from app.repository.user import UserRepository, UserNotFoundError
from app.schemas.user import UserAuthSchema, UserSessionCreateSchema, UserSession
from app.utils.hash_pwd import PasswordNotValidError
from redis import asyncio as redis


logger = logging.getLogger(__name__)

user_router = APIRouter(prefix="/v1/users")


@user_router.post("/register")
async def register_user(
        user_data: UserAuthSchema,
        connection: asyncpg.Connection = Depends(get_db_connection)
):
    user_id: int | None = await UserRepository.create_user(connection, user_data)
    if user_id is None:
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
):
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
        content=f"Пользователь авторизован: {repr(user_session)}",
        status_code=201
    )

    response.set_cookie(key="sessionToken", value=user_session.model_dump_json(indent=None))

    return response


@user_router.post("/logout")
async def logout(
        request: Request,
        connection: asyncpg.Connection = Depends(get_db_connection),
        redis_conn: redis.Redis = Depends(get_redis)
):
    try:
        session_cookie = request.cookies.get("sessionToken")
        if session_cookie is None:
            return JSONResponse(content="Сессия не найдена", status_code=200)

        session_model = UserSession.model_validate_json(session_cookie)
        await PostgresSessionRepository.delete_session(connection, session_model)
        await RedisSessionRepository.delete_session(redis_conn, session_model)
    finally:
        return JSONResponse(
            content="Сессия закрыта",
            status_code=200
        )
