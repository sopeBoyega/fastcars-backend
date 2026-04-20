from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class BookingStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"


class BookingCreate(BaseModel):
    car_id: str
    start_date: date
    end_date: date

    @field_validator("car_id")
    @classmethod
    def clean_car_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Car id is required")
        return value

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, value: date, info) -> date:
        start_date = info.data.get("start_date")
        if start_date and value < start_date:
            raise ValueError("End date must be on or after start date")
        return value


class BookingOut(BaseModel):
    booking_ref: str = Field(alias="_id")
    customer: str | None = Field(alias="user_name")
    car_name: str | None = None
    start_date: date
    end_date: date
    status: BookingStatus
    total_cost: float = Field(alias="total_price")
    user_id: str
    user_email: str | None = None
    car_id: str
    total_days: int
    created_at: datetime
