import logging
from datetime import datetime
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


def expire_token_check(expire_token: datetime) -> bool:
    logger.info("expire_token: %s", expire_token)

    current_time = datetime.now(ZoneInfo("Europe/Moscow"))
    logger.info("current_time: %s", current_time)

    return current_time < expire_token
