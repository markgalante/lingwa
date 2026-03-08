import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.schemas.language import LanguageRead


class UserCreate(BaseModel):
    email: EmailStr
    name: str | None = None


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


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
