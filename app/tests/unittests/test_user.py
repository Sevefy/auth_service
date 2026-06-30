from datetime import datetime, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest

from app.schemas.user import UserSession
from app.utils.user_utils import generate_key_by_user


@pytest.fixture()
def user():
    return UserSession(
        user_id=1,
        expire_token=datetime.now(ZoneInfo("Europe/Moscow")) + timedelta(hours=1),
        username="username",
        token=uuid4(),
        id=1
    )

def test_generate_key_by_user(user):
    key = generate_key_by_user(user)
    assert str(user.token) == key