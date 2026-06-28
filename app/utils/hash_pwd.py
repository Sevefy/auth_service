from datetime import datetime
from zoneinfo import ZoneInfo

from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)

class PasswordNotValidError(Exception):
    pass

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__memory_cost=65536, # 64MB
    argon2__time_cost=3,
    argon2__parallelism=4
)

def hash_password(value: str) -> str:
    return pwd_context.hash(value)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return  pwd_context.verify(plain_password, hashed_password)

def expire_token_check(expire_token: datetime) -> bool:
    logger.info("expire_token: %s", expire_token)

    current_time = datetime.now(ZoneInfo("Europe/Moscow"))
    logger.info("current_time: %s", current_time)

    return True if current_time < expire_token else False