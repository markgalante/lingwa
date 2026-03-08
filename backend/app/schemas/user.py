import uuid
from datetime import datetime
from typing import Self

from pydantic import BaseModel, EmailStr, Field, model_validator

from app.schemas.language import LanguageRead


class UserCreate(BaseModel):
    email: EmailStr
    name: str | None = None


class UserRegister(BaseModel):
    email: EmailStr


class CompleteRegistration(BaseModel):
    token: str
    name: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=8)
    confirm_password: str

    @model_validator(mode="after")
    def passwords_match(self) -> Self:
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password: str = Field(min_length=8)
    confirm_password: str

    @model_validator(mode="after")
    def passwords_match(self) -> Self:
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    message: str


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
