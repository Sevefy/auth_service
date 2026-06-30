import logging
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import asyncpg
from asyncpg import DataError, PostgresError
from asyncpg.protocol.record import Record

from app.config.settings import settings
from app.schemas.user import UserSession, UserSessionCreateSchema

logger = logging.getLogger(__name__)


class SessionNotFoundError(Exception):
    pass


class TokenExpireError(Exception):
    pass


class PostgresSessionRepository:

    @staticmethod
    async def create_session(connection: asyncpg.Connection, user_data: UserSessionCreateSchema) -> UserSession | None:
        token = uuid.uuid4()
        expire_token = datetime.now(ZoneInfo("Europe/Moscow")) + timedelta(hours=settings.token_lifetime_hours)
        sql = """
            INSERT INTO sessions(user_id, token, expire_token)
            VALUES ($1, $2, $3)
            RETURNING id
        """
        try:
            async with connection.transaction():
                record: Record | None = await connection.fetchrow(sql, user_data.id, token, expire_token)
            if record is None or record.get("id") is None:
                return None
            logger.info(
                "Postgres create session for %s: %s. Time expire: %s",
                user_data.username, token, expire_token
            )
            return UserSession(
                id=record.get("id"),
                token=token,
                username=user_data.username,
                user_id=user_data.id,
                expire_token=expire_token
            )
        except PostgresError as e:
            # PostgresError - базовое исключение для всех ошибок движка PostgreSQL
            logger.error(f"Внутренняя ошибка базы данных: {e}")
            raise

    @staticmethod
    async def delete_session(connection: asyncpg.Connection, session_token: str) -> None:
        sql = """
            DELETE FROM sessions
            WHERE token=$1;
        """

        try:
            async with connection.transaction():
                await connection.execute(sql, session_token)
            logger.info("Postgres delete session: %s", session_token)
        except PostgresError as e:
            # PostgresError - базовое исключение для всех ошибок движка PostgreSQL
            logger.error(f"Внутренняя ошибка базы данных: {e}")
            raise

    @staticmethod
    async def find_session(connection: asyncpg.Connection, session_token: str) -> UserSession | None:
        sql = """
            SELECT sessions.id, token, expire_token, users.username, user_id 
            FROM sessions
            JOIN users ON users.id = user_id
            WHERE token=$1;
        """

        try:
            logger.info(
                "Поиск сессии пользователя в БД: %s",
                session_token
            )
            async with connection.transaction():
                record: Record | None = await connection.fetchrow(sql, session_token)
            if record is None:
                raise SessionNotFoundError("Сессия не найдена")
            logger.info("Найдена сессия пользователя: %s", record.get("token"))

            user_session = UserSession(
                id=record.get("id"),
                user_id=record.get("user_id"),
                expire_token=record.get("expire_token", datetime.min).astimezone(ZoneInfo("Europe/Moscow")),
                token=record.get("token"),
                username=record.get("username"),
            )

            return user_session
        except DataError as e:
            logger.error("Ошибка в запросе: %s", str(e))
            return None
        except PostgresError as e:
            # PostgresError - базовое исключение для всех ошибок движка PostgreSQL
            logger.error(f"Внутренняя ошибка базы данных: {e}")
            raise

    @staticmethod
    async def truncate_all_sessions(connection: asyncpg.Connection) -> None:
        sql = """
            TRUNCATE TABLE sessions CONTINUE IDENTITY RESTRICT;
        """
        try:
            async with connection.transaction():
                await connection.execute(sql)
            logger.info("Sessions TRUNCATE complete!")
        except PostgresError as e:
            # PostgresError - базовое исключение для всех ошибок движка PostgreSQL
            logger.error(f"Внутренняя ошибка базы данных: {e}")
            raise
