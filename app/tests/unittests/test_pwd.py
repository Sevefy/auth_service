
from app.utils.pwd_utils import hash_password, verify_password


def test_hash_password():
    password = "12345"
    hashed_password = hash_password(password)
    assert password != hashed_password

def test_verify_password_ok():
    password = "12345"
    hashed_password = hash_password(password)
    assert verify_password(password, hashed_password)

def test_verify_password_fail():
    password = "12345"
    hashed_password = hash_password(password)

    fail_password = "123456"
    assert not verify_password(fail_password, hashed_password)