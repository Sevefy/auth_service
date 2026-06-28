from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict
from dataclasses import dataclass

class UserAuthSchema(BaseModel):
    username: str = Field(max_length=50)
    password: str = Field(max_length=128)

class UserSessionCreateSchema(BaseModel):
    id: int
    username: str = Field(max_length=50)

class UserSession(BaseModel):
    id: int
    token: UUID
    username: str
    user_id: int
    expire_token: datetime
    model_config = ConfigDict(frozen=True)