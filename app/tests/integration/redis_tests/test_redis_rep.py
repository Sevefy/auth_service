import pytest

from app.repository.redis_session_repository import RedisSessionRepository
from app.schemas.user import UserSession


@pytest.mark.redis_rep
@pytest.mark.asyncio
async def test_set_and_get_session(redis_con, user_session: UserSession):
    await RedisSessionRepository.set_session(redis_con, user_session)
    session_token = str(user_session.token)
    session_from_redis = await RedisSessionRepository.get_session(redis_con, session_token)
    assert isinstance(session_from_redis, UserSession)
    assert session_from_redis == user_session


@pytest.mark.redis_rep
@pytest.mark.asyncio
async def test_get_session_not_found(
        redis_con,
        user_session: UserSession,
        other_session: UserSession
):
    await RedisSessionRepository.set_session(redis_con, user_session)
    session_token = str(other_session.token)
    session_from_redis = await RedisSessionRepository.get_session(redis_con, session_token)
    assert session_from_redis is None


@pytest.mark.redis_rep
@pytest.mark.asyncio
async def test_delete_session(
        redis_con,
        user_session: UserSession
):
    await RedisSessionRepository.set_session(redis_con, user_session)
    session_token = str(user_session.token)
    await RedisSessionRepository.delete_session(redis_con, session_token)

    session_from_redis = await RedisSessionRepository.get_session(redis_con, session_token)
    assert session_from_redis is None
