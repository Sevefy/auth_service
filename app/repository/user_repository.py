import asyncio
import logging

import asyncpg
from asyncpg.exceptions import PostgresError, UniqueViolationError

from app.schemas.user import UserAuthSchema, UserSessionCreateSchema
from app.utils.pwd_utils import PasswordNotValidError, hash_password, verify_password

logger = logging.getLogger(__name__)


class UserNotFoundError(Exception):
    pass


class UserRepository:

    @staticmethod
    async def create_user(connection: asyncpg.Connection, user_data: UserAuthSchema) -> int | None:
        sql = """
            INSERT INTO users(username, password) 
            VALUES ($1, $2) 
            RETURNING id;
        """
        password = await asyncio.to_thread(hash_password, user_data.password)
        try:
            async with connection.transaction():
                record: asyncpg.Record | None = await connection.fetchrow(sql, user_data.username, password)
            return record["id"] if record else None

        except UniqueViolationError:
            logger.warning(f"Ошибка регистрации: пользователь '{user_data.username}' уже существует.")
            raise
        except PostgresError as e:
            # PostgresError - базовое исключение для всех ошибок движка PostgreSQL
            logger.error(f"Внутренняя ошибка базы данных: {e}")
            raise

    @staticmethod
    async def auth_user(connection: asyncpg.Connection, user_data: UserAuthSchema) -> UserSessionCreateSchema:
        sql = """
            SELECT id, username, password
            FROM users
            WHERE username=$1
        """

        try:
            async with connection.transaction():
                record: asyncpg.Record | None = await connection.fetchrow(sql, user_data.username)
            if record is None:
                raise UserNotFoundError("Пользователь с таким username не найден")

            hashed_password: str | None = record.get("password", None)
            if hashed_password and not verify_password(user_data.password, hashed_password):
                raise PasswordNotValidError("Не верный пароль")

            return UserSessionCreateSchema(id=record["id"], username=record["username"])
        except PostgresError as e:
            # PostgresError - базовое исключение для всех ошибок движка PostgreSQL
            logger.error(f"Внутренняя ошибка базы данных: {e}")
            raise