from fastapi import FastAPI
import uvicorn

from app.config import database, cache as redis
from app.config.logger import config_logging
from app.config.settings import settings
from app.middleware.session_middleware import SessionMiddleware
from app.routes.router import router
from app.repository.postgres_session import PostgresSessionRepository


from contextlib import asynccontextmanager
import logging

config_logging()

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app_fast_api: FastAPI):
    app_fast_api.state.db_pool = await database.init_db_pool()
    app_fast_api.state.redis_pool = redis.init_redis_pool()
    logger.info("Init DB %s", app_fast_api.state.db_pool)
    logger.info("Init redis %s", app_fast_api.state.redis_pool)
    yield
    async with app_fast_api.state.db_pool.acquire() as connection:
        await PostgresSessionRepository.truncate_all_sessions(connection)
    await app_fast_api.state.db_pool.close()
    await app_fast_api.state.redis_pool.disconnect()

    logger.info("Close connection DB")
    logger.info("Close connection Redis")

app = FastAPI(
    title="Сервис аутентификации",
    description="Практическое задание по созданию микросервиса для аутентификации пользователей",
    version="0.1.0",
    lifespan=lifespan
)
app.include_router(router=router)
app.add_middleware(SessionMiddleware)

if __name__ == "__main__":

    logger.info(settings.model_dump())

    uvicorn.run("app.run:app", host=settings.host, port=settings.port, reload=True)