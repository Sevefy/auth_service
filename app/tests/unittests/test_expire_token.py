from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.utils.token_utils import expire_token_check


def test_expire_token_check_valid():
    expire_token = datetime.now(ZoneInfo("Europe/Moscow")) + timedelta(hours=1)
    assert expire_token_check(expire_token)

def test_expire_token_check_invalid():
    expire_token = datetime.now(ZoneInfo("Europe/Moscow")) - timedelta(hours=1)
    assert not expire_token_check(expire_token)

