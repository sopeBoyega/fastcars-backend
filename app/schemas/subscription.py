from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class SubscriptionCreate(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def clean_email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("Enter a valid email address")
        return value


class SubscriptionOut(BaseModel):
    id: str = Field(alias="_id")
    email: str
    created_at: datetime
