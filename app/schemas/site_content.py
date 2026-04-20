from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class SiteContentUpdate(BaseModel):
    value: str = Field(min_length=1, max_length=10000)

    @field_validator("value")
    @classmethod
    def clean_value(cls, value: str) -> str:
        return value.strip()


class SiteContentOut(BaseModel):
    id: str = Field(alias="_id")
    key: str
    value: str
    updated_at: datetime
