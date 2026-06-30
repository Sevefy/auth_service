import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
import pytest_asyncio
from redis import asyncio as redis

from app.config.cache import init_redis_pool
from app.config.settings import SettingsRedis, settings
from app.schemas.user import UserSession


@pytest.fixture(autouse=True)
def test_redis_settings(monkeypatch):
    monkeypatch.setattr(settings, "redis", SettingsRedis(
        host="localhost",
        port=6380,
        password="rpassword",
        user="ruser"
    ))

@pytest_asyncio.fixture()
async def pool(test_redis_settings):
    pool = init_redis_pool()
    yield pool
    await pool.disconnect()

@pytest_asyncio.fixture()
async def redis_con(pool):
    async with redis.Redis(connection_pool=pool) as connection:
        yield connection

@pytest.fixture()
def user_session():
    return UserSession(
        id=1,
        user_id=1,
        username="username",
        token=uuid.uuid4(),
        expire_token=datetime.now(ZoneInfo("Europe/Moscow"))
    )

@pytest.fixture()
def other_session():
    return UserSession(
        id=2,
        user_id=2,
        username="username2",
        token=uuid.uuid4(),
        expire_token=datetime.now(ZoneInfo("Europe/Moscow"))
    )
