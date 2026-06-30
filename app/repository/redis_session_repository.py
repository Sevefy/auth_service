import logging
from datetime import timedelta

from redis import asyncio as redis

from app.config.settings import settings
from app.schemas.user import UserSession
from app.utils.user_utils import generate_key_by_user

logger = logging.getLogger(__name__)


class RedisSessionRepository:
    @staticmethod
    async def set_session(connection: redis.Redis, user_data: UserSession) -> None:
        key = generate_key_by_user(user_data)
        value = user_data.model_dump_json(indent=None)
        logger.info("Redis set cache by key=%s: %s", key, value)

        await connection.set(
            key,
            value,
            ex=timedelta(hours=settings.token_lifetime_hours + 0.25)
        )

    @staticmethod
    async def get_session(connection: redis.Redis, session_token: str) -> UserSession | None:
        session_json = await connection.get(session_token)
        session_schema = None
        if session_json is not None:
            session_schema = UserSession.model_validate_json(session_json)
        logger.info("Redis get cache by token=%s", session_token)
        return None or session_schema

    @staticmethod
    async def delete_session(connection: redis.Redis, session_token: str) -> None:
        logger.info("Redis delete cache by key=%s", session_token)
        await connection.delete(session_token)