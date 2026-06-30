from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SettingsDB(BaseModel):
    model_config = SettingsConfigDict(
        env_prefix=""  # убираем префикс, так как будем использовать вложенность
    )
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    database: str = Field(...)
    user: str = Field(...)
    password: str = Field(...)

class SettingsRedis(BaseModel):
    model_config = SettingsConfigDict(
        env_prefix=""  # убираем префикс, так как будем использовать вложенность
    )
    host: str = Field(default="localhost")
    port: int = Field(default=6379)
    user: str = Field(...)
    password: str = Field(...)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="",
        env_nested_delimiter="__",
        env_file = ".env",  # указываем файл .env
        env_file_encoding="utf-8",
    )
    host: str = Field(default="localhost")
    port: int = Field(default=8081)
    token_lifetime_hours: float = Field(default=1)
    db: SettingsDB
    redis: SettingsRedis


settings = Settings()