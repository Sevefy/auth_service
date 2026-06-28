import logging
from datetime import timedelta, datetime

from redis import asyncio as redis

from app.config.settings import settings
from app.schemas.user import UserSession

logger = logging.getLogger(__name__)


def generate_key_by_user(user: UserSession) -> str:
    return str(user.token)


class RedisSessionRepository:
    @staticmethod
    async def set_session(connection: redis.Redis, user_data: UserSession) -> None:
        key = generate_key_by_user(user_data)
        value = user_data.expire_token.strftime("%Y-%m-%d %H:%M:%S %z")
        logger.info("Redis set cache by key=%s: %s", key, value)

        await connection.set(
            key,
            value,
            ex=timedelta(hours=settings.token_lifetime_hours + 0.25)
        )

    @staticmethod
    async def get_session(connection: redis.Redis, user_data: UserSession) -> bytes | str | None:
        key = generate_key_by_user(user_data)
        session = await connection.get(key)
        logger.info("Redis get cache by key=%s: %s", key, session)
        return session

    @staticmethod
    async def delete_session(connection: redis.Redis, user_data: UserSession) -> None:
        key = generate_key_by_user(user_data)
        logger.info("Redis delete cache by key=%s", key)
        await connection.delete(key)