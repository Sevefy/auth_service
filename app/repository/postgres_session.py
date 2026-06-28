import logging
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import asyncpg
from asyncpg import PostgresError
from asyncpg.protocol.record import Record

from app.config.settings import settings
from app.schemas.user import UserSessionCreateSchema, UserSession

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
    async def delete_session(connection: asyncpg.Connection, session: UserSession) -> None:
        sql = """
            DELETE FROM sessions
            WHERE id=$1;
        """

        try:
            await connection.fetch(sql, session.id)
            logger.info("Postgres delete session: %s, %s", session.id, session.token)
        except PostgresError as e:
            # PostgresError - базовое исключение для всех ошибок движка PostgreSQL
            logger.error(f"Внутренняя ошибка базы данных: {e}")
            raise

    @staticmethod
    async def find_session(connection: asyncpg.Connection, session: UserSession) -> datetime | None:
        sql = """
            SELECT id, token, expire_token FROM sessions
            WHERE id=$1 AND token=$2 AND user_id=$3;
        """

        try:
            record: Record | None = await connection.fetchrow(sql, session.id, session.token, session.user_id)
            if record is None:
                raise SessionNotFoundError("Сессия не найдена")

            return record.get("expire_token", datetime.min).astimezone(ZoneInfo("Europe/Moscow"))

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
            await connection.fetchrow(sql)
            logger.info("Sessions TRUNCATE complete!")
        except PostgresError as e:
            # PostgresError - базовое исключение для всех ошибок движка PostgreSQL
            logger.error(f"Внутренняя ошибка базы данных: {e}")
            raise
