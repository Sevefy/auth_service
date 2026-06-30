import httpx
import pytest
import pytest_asyncio
from redis import asyncio as redis

from app.config.cache import init_redis_pool
from app.config.database import init_db_pool
from app.config.settings import SettingsDB, SettingsRedis, settings
from app.run import app


@pytest.fixture(autouse=True)
def test_settings(monkeypatch):
    monkeypatch.setattr(settings, "db", SettingsDB(
        host="localhost",
        port=5432,
        user="admin",
        password="admin",
        database="test_auth_user"
    ))


    monkeypatch.setattr(settings, "redis", SettingsRedis(
        host="localhost",
        port=6380,
        password="rpassword",
        user="ruser"
    ))

@pytest_asyncio.fixture()
async def postgres_pool(test_settings):
    pool = await init_db_pool()
    yield pool
    await pool.close()

@pytest_asyncio.fixture()
async def redis_pool(test_settings):
    pool = init_redis_pool()
    yield pool
    await pool.disconnect()


@pytest_asyncio.fixture()
async def pg_con(postgres_pool):
    async with postgres_pool.acquire() as connection:
        yield connection

@pytest_asyncio.fixture()
async def redis_con(redis_pool):
    async with redis.Redis(connection_pool=redis_pool) as con:
        yield con

@pytest_asyncio.fixture(autouse=True)
async def cleanup_db(pg_con):
    """Очищает таблицу users после каждого теста"""
    yield
    await pg_con.execute("TRUNCATE TABLE users CASCADE")

@pytest_asyncio.fixture()
async def client(postgres_pool, redis_pool, cleanup_db):
    app.state.db_pool = postgres_pool
    app.state.redis_pool = redis_pool
    transport = httpx.ASGITransport(app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


BASE_URL_PRIVATE = "/api/v1/other"
BASE_URL_PUBLIC = "/api/v1/users"
USER_DATA = {
    "username": "username",
    "password": "password123"
}


async def register(client, user_data):
    response = await client.post(url=BASE_URL_PUBLIC + "/register", json=user_data)
    return response


async def auth(client, user_data):
    response = await client.post(url=BASE_URL_PUBLIC + "/auth", json=user_data)
    return response


async def register_and_auth(client, user_data):
    await client.post(url=BASE_URL_PUBLIC + "/register", json=user_data)
    response = await client.post(url=BASE_URL_PUBLIC + "/auth", json=user_data)
    return response
