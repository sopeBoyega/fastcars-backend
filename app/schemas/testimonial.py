from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class TestimonialCreate(BaseModel):
    message: str = Field(min_length=10, max_length=1000)

    @field_validator("message")
    @classmethod
    def clean_message(cls, value: str) -> str:
        return value.strip()


class TestimonialUpdate(BaseModel):
    is_active: bool


class TestimonialOut(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    user_name: str
    message: str
    is_active: bool
    created_at: datetime
