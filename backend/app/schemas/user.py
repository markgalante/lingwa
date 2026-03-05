import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.schemas.language import LanguageRead


class UserCreate(BaseModel):
    email: EmailStr
    name: str | None = None


class UserUpdate(BaseModel):
    name: str | None = None
    avatar_url: str | None = None


class UserRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: EmailStr
    name: str | None
    is_verified: bool
    avatar_url: str | None
    languages: list[LanguageRead] = []
    created_at: datetime
    updated_at: datetime
