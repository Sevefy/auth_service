import logging
from abc import ABC, abstractmethod

import redis.asyncio as redis
from fastapi.requests import Request

from app.repository.postgres_session_repository import PostgresSessionRepository
from app.repository.redis_session_repository import RedisSessionRepository
from app.schemas.user import UserSession
from app.utils.token_utils import expire_token_check

logger = logging.getLogger(__name__)


class ValidateSession(ABC):

    @staticmethod
    @abstractmethod
    async def validate_session(request: Request, session_token: str) -> UserSession | None: pass


class RedisValidateSession(ValidateSession):

    @staticmethod
    async def validate_session(request: Request, session_token: str) -> UserSession | None:
        pool = request.app.state.redis_pool
        async with redis.Redis(connection_pool=pool) as connection:
            session_from_redis = await RedisSessionRepository.get_session(connection, session_token)

            if session_from_redis is None or not isinstance(session_from_redis, UserSession):
                return None
            logger.info("sessionToken from redis: %s", session_from_redis)
            if not expire_token_check(session_from_redis.expire_token):
                await RedisSessionRepository.delete_session(connection, session_token)
                return None
            return session_from_redis


class PostgresValidateSession(ValidateSession):

    @staticmethod
    async def validate_session(request: Request, session_token: str) -> UserSession | None:
        db_pool = request.app.state.db_pool
        redis_pool = request.app.state.redis_pool
        async with db_pool.acquire() as connection:
            user_session = await PostgresSessionRepository.find_session(connection, session_token)

            if user_session is None:
                return None

            logger.info("user_session from db: %s", user_session)
            if not expire_token_check(user_session.expire_token):
                await PostgresSessionRepository.delete_session(connection, session_token)
                return None

            async with redis.Redis(connection_pool=redis_pool) as con:
                await RedisSessionRepository.set_session(con, user_session)
            return user_session

class SessionValidationChain:
    def __init__(self, request: Request, session_token: str):
        self.strategies = [
            RedisValidateSession,
            PostgresValidateSession
        ]
        self.req = request
        self.session = session_token

    async def validate(self) -> UserSession | None:
        for strategy in self.strategies:
            user_session = await strategy.validate_session(self.req, self.session)
            if user_session is not None:
                return user_session
        return None
