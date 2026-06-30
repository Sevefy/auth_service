import pytest

from app.repository.redis_session_repository import RedisSessionRepository
from app.schemas.user import UserSession
from app.tests.integration.api_tests.conftest import BASE_URL_PRIVATE, USER_DATA, register_and_auth


@pytest.mark.test_cache_aside
@pytest.mark.asyncio
async def test_session_in_cache(client, redis_con):

    await register_and_auth(client, USER_DATA)

    token_cookie = client.cookies.get("sessionToken")
    session_cache = await redis_con.get(token_cookie)
    assert session_cache is not None

    user_session = UserSession.model_validate_json(session_cache)
    assert str(user_session.token) == token_cookie

@pytest.mark.test_cache_aside
@pytest.mark.asyncio
async def test_session_delete_cache(client, redis_con):

    await register_and_auth(client, USER_DATA)

    token_cookie = client.cookies.get("sessionToken")
    session_cache = await redis_con.get(token_cookie)
    assert session_cache is not None

    await RedisSessionRepository.delete_session(redis_con, token_cookie)
    session_cache = await redis_con.get(token_cookie)
    assert session_cache is None

@pytest.mark.test_cache_aside
@pytest.mark.asyncio
async def test_session_regenerate_cache(client, redis_con):
    await register_and_auth(client, USER_DATA)

    # проверка кэша
    token_cookie = client.cookies.get("sessionToken")
    session_cache = await redis_con.get(token_cookie)
    assert session_cache is not None

    # Удалили сессию из кэша
    await RedisSessionRepository.delete_session(redis_con, token_cookie)
    session_cache = await redis_con.get(token_cookie)
    assert session_cache is None

    # Опять поставили сессию после обращения к private и наличии куки

    response = await client.get(url=BASE_URL_PRIVATE + "/")

    assert response.status_code == 200
    session_cache = await redis_con.get(token_cookie)
    assert session_cache is not None