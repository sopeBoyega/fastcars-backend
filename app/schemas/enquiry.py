from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class EnquiryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str
    message: str = Field(min_length=10, max_length=2000)

    @field_validator("name", "message")
    @classmethod
    def clean_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("email")
    @classmethod
    def clean_email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("Enter a valid email address")
        return value


class EnquiryOut(BaseModel):
    id: str = Field(alias="_id")
    name: str
    email: str
    message: str
    created_at: datetime
