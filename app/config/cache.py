from typing import AsyncGenerator

import redis.asyncio as redis
from fastapi import Request, HTTPException, status

from app.config.settings import settings


def init_redis_pool():
    pool = redis.ConnectionPool(
        host=settings.redis.host,
        port=settings.redis.port,
        password=settings.redis.password,
        username=settings.redis.user,
        db=0,
        max_connections=50,  # Maximum connections in the pool
        decode_responses=True,
        socket_timeout=5.0,
        socket_connect_timeout=5.0,
        retry_on_timeout=True
    )
    return pool


async def get_redis(request: Request) -> AsyncGenerator[redis.Redis, None]:
    pool: redis.ConnectionPool | None = getattr(request.app.state, "redis_pool", None)
    if pool is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database pool is not initialized"
        )

    async with redis.Redis(connection_pool=pool) as client:
        yield client
