from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
import pytest_asyncio

from app.config.database import init_db_pool
from app.config.settings import SettingsDB, settings
from app.repository.postgres_session_repository import PostgresSessionRepository
from app.repository.user_repository import UserRepository
from app.schemas.user import UserAuthSchema, UserSession, UserSessionCreateSchema


@pytest.fixture(autouse=True)
def test_db_settings(monkeypatch):
    monkeypatch.setattr(settings, "db", SettingsDB(
        host="localhost",
        port=5432,
        user="admin",
        password="admin",
        database="test_auth_user"
    ))

@pytest_asyncio.fixture()
async def pool(test_db_settings):
    pool = await init_db_pool()
    yield pool
    await pool.close()

@pytest_asyncio.fixture()
async def pg_con(pool):
    async with pool.acquire() as connection:
        yield connection

@pytest_asyncio.fixture(autouse=True)
async def cleanup_db(pg_con):
    """Очищает таблицу users после каждого теста"""
    yield
    await pg_con.execute("TRUNCATE TABLE users CASCADE")


@pytest_asyncio.fixture()
async def create_user(pg_con):
    async def user_db(user_data: UserAuthSchema):
        user = await UserRepository.create_user(pg_con, user_data)
        return user
    return user_db


@pytest.fixture()
def user_sam():
    return UserAuthSchema(
        username="Sam",
        password="12345"
    )


@pytest.fixture()
def user_nick():
    return UserAuthSchema(
        username="Nick",
        password="12345"
    )

@pytest.fixture()
def other_session():
    return UserSession(
        id=2,
        token=uuid4(),
        username="other",
        user_id=13,
        expire_token=datetime.now(ZoneInfo("Europe/Moscow")),
    )

@pytest_asyncio.fixture()
async def user_session(create_user, pg_con, user_sam):
    user_db = await create_user(user_sam)
    assert isinstance(user_db, int)

    user_session_schema = UserSessionCreateSchema(
        id=user_db,
        username=user_sam.username
    )
    session = await PostgresSessionRepository.create_session(pg_con, user_session_schema)
    return session