import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator


class LanguageCreate(BaseModel):
    name: str
    code: str

    @field_validator("code")
    @classmethod
    def code_lowercase(cls, v: str) -> str:
        return v.lower().strip()


class LanguageRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    code: str
    created_at: datetime
