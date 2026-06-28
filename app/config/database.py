import logging
from typing import AsyncGenerator

import asyncpg
from fastapi import Request, HTTPException, status

from app.config.settings import settings

logger = logging.getLogger(__name__)


async def init_db_pool() -> asyncpg.Pool:
    # Логируем параметры до старта (защита от неверного парсинга)
    logger.info(f"Connecting to Postgres at {settings.db.host}:{settings.db.port}, DB: {settings.db.database}")

    pool = await asyncpg.create_pool(
        host=settings.db.host,
        port=settings.db.port,
        user=settings.db.user,
        password=settings.db.password,
        database=settings.db.database,
        min_size=6,
        max_size=20
    )

    if pool is None:
        raise RuntimeError("Failed to create database pool")

    return pool


async def get_db_connection(request: Request) -> AsyncGenerator[asyncpg.Connection, None]:
    pool: asyncpg.Pool | None = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database pool is not initialized"
        )
    async with pool.acquire() as connection:
        yield connection
