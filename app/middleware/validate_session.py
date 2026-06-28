import logging
from abc import ABC, abstractmethod
from datetime import datetime

from fastapi.requests import Request

from app.repository.redis_session import RedisSessionRepository
from app.repository.postgres_session import PostgresSessionRepository
from app.schemas.user import UserSession
import redis.asyncio as redis

from app.utils.hash_pwd import expire_token_check

logger = logging.getLogger(__name__)


class ValidateSession(ABC):

    @staticmethod
    @abstractmethod
    async def validate_session(request: Request, session_user: UserSession) -> bool: pass


class RedisValidateSession(ValidateSession):

    @staticmethod
    async def validate_session(request: Request, session_user: UserSession) -> bool:
        pool = request.app.state.redis_pool
        async with redis.Redis(connection_pool=pool) as connection:
            session_from_redis = await RedisSessionRepository.get_session(connection, session_user)

            if session_from_redis is None or not isinstance(session_from_redis, str):
                return False
            logger.info("sessionToken from redis: %s", session_from_redis)
            expire_session = datetime.strptime(session_from_redis, "%Y-%m-%d %H:%M:%S %z")
            if not expire_token_check(expire_session):
                await RedisSessionRepository.delete_session(connection, session_user)
                return False
            return True


class PostgresValidateSession(ValidateSession):

    @staticmethod
    async def validate_session(request: Request, session_user: UserSession) -> bool:
        db_pool = request.app.state.db_pool
        redis_pool = request.app.state.redis_pool
        async with db_pool.acquire() as connection:
            expire_token_from_db = await PostgresSessionRepository.find_session(connection, session_user)

            if expire_token_from_db is None:
                return False

            logger.info("sessionToken from db: %s", expire_token_from_db)
            if not expire_token_check(expire_token_from_db):
                await PostgresSessionRepository.delete_session(connection, session_user)
                return False

            async with redis.Redis(connection_pool=redis_pool) as con:
                await RedisSessionRepository.set_session(con, session_user)
            return True

class SessionValidationChain:
    def __init__(self, request: Request, session_user: UserSession):
        self.strategies = [
            RedisValidateSession,
            PostgresValidateSession
        ]
        self.req = request
        self.session = session_user

    async def validate(self) -> bool:
        for strategy in self.strategies:
            is_valid = await strategy.validate_session(self.req, self.session)
            if is_valid:
                return True
        return False
