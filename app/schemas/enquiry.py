from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class EnquiryStatus(str, Enum):
    unread = "unread"
    read = "read"


class EnquiryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str
    phone: str | None = Field(default=None, max_length=30)
    message: str = Field(min_length=10, max_length=2000)

    @field_validator("name", "message")
    @classmethod
    def clean_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("phone")
    @classmethod
    def clean_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("email")
    @classmethod
    def clean_email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("Enter a valid email address")
        return value


class EnquiryUpdate(BaseModel):
    status: EnquiryStatus


class EnquiryOut(BaseModel):
    id: str = Field(alias="_id")
    name: str
    email: str
    phone: str | None = None
    message: str
    status: EnquiryStatus
    created_at: datetime
