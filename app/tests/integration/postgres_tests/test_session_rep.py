import pytest

from app.config.settings import settings
from app.repository.postgres_session_repository import PostgresSessionRepository, SessionNotFoundError
from app.schemas.user import UserAuthSchema, UserSession, UserSessionCreateSchema
from app.utils.token_utils import expire_token_check


@pytest.mark.session_rep
@pytest.mark.asyncio
async def test_create_session_ok(user_session, user_sam: UserAuthSchema, pg_con):
    assert isinstance(user_session, UserSession)


@pytest.mark.session_rep
@pytest.mark.asyncio
async def test_find_session_ok(user_session, user_sam: UserAuthSchema, pg_con):
    session_token = str(user_session.token)
    user_session = await PostgresSessionRepository.find_session(pg_con, session_token)
    assert user_session is not None
    assert isinstance(user_session, UserSession)


@pytest.mark.session_rep
@pytest.mark.asyncio
async def test_find_session_not_found(
        pg_con,
        other_session
):
    session_token = str(other_session.token)

    with pytest.raises(SessionNotFoundError):
        await PostgresSessionRepository.find_session(pg_con, session_token)


@pytest.mark.session_rep
@pytest.mark.asyncio
async def test_delete_session(user_session, user_sam: UserAuthSchema, pg_con):
    session_token = str(user_session.token)
    await PostgresSessionRepository.delete_session(pg_con, session_token)
    with pytest.raises(SessionNotFoundError):
        await PostgresSessionRepository.find_session(pg_con, session_token)


@pytest.mark.session_rep
@pytest.mark.asyncio
async def test_token_expire(
        monkeypatch,
        create_user,
        user_sam: UserAuthSchema,
        pg_con,
):
    monkeypatch.setattr(settings, "token_lifetime_hours", -0.1)

    user_db = await create_user(user_sam)
    user_session_schema = UserSessionCreateSchema(
        id=user_db,
        username=user_sam.username
    )
    session = await PostgresSessionRepository.create_session(pg_con, user_session_schema)

    assert not expire_token_check(session.expire_token)


@pytest.mark.session_rep
@pytest.mark.asyncio
async def test_truncate_sessions(
        create_user,
        user_sam: UserAuthSchema,
        pg_con
):
    sessions = []
    user_db = await create_user(user_sam)

    user_session_schema = UserSessionCreateSchema(
        id=user_db,
        username=user_sam.username
    )

    for _ in range(10):
        session = await PostgresSessionRepository.create_session(
            pg_con, user_session_schema
        )
        sessions.append(session)

    await PostgresSessionRepository.truncate_all_sessions(pg_con)
    with pytest.raises(SessionNotFoundError):
        for session in sessions:
            session_token = str(session.token)
            await PostgresSessionRepository.find_session(pg_con, session_token)
