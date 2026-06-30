import pytest
from asyncpg.exceptions import UniqueViolationError

from app.repository.user_repository import UserNotFoundError, UserRepository
from app.utils.pwd_utils import PasswordNotValidError


@pytest.mark.user_rep
@pytest.mark.asyncio
async def test_create_user(create_user, user_sam):
    user_db = await create_user(user_sam)
    assert isinstance(user_db, int)


@pytest.mark.user_rep
@pytest.mark.asyncio
async def test_create_user_duplicate(create_user, user_sam):
    user_db = await create_user(user_sam)
    assert isinstance(user_db, int)
    with pytest.raises(UniqueViolationError):
        user_duplicate = await create_user(user_sam)
        assert user_duplicate is None


@pytest.mark.user_rep
@pytest.mark.asyncio
async def test_auth_user_ok(create_user, user_sam, pg_con):
    user_db = await create_user(user_sam)
    assert isinstance(user_db, int)

    user_session = await UserRepository.auth_user(pg_con, user_sam)

    assert user_session.username == user_sam.username


@pytest.mark.user_rep
@pytest.mark.asyncio
async def test_auth_user_not_found(
        create_user,
        user_sam,
        user_nick,
        pg_con
):
    user_db = await create_user(user_sam)
    assert isinstance(user_db, int)

    with pytest.raises(UserNotFoundError):
        await UserRepository.auth_user(pg_con, user_nick)


@pytest.mark.user_rep
@pytest.mark.asyncio
async def test_auth_user_wrong_password(
        create_user,
        user_sam,
        pg_con
):
    user_db = await create_user(user_sam)
    assert isinstance(user_db, int)
    user_sam.password = "other"
    with pytest.raises(PasswordNotValidError):
        await UserRepository.auth_user(pg_con, user_sam)
