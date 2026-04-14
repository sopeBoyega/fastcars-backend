from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class CarCategory(str, Enum):
    economy = "Economy"
    premium = "Premium"
    suv = "SUV"
    luxury = "Luxury"


class TransmissionType(str, Enum):
    automatic = "Automatic"
    manual = "Manual"


class FuelType(str, Enum):
    petrol = "Petrol"
    diesel = "Diesel"
    electric = "Electric"
    hybrid = "Hybrid"


class BrandCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    logo_url: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("logo_url")
    @classmethod
    def clean_logo_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class BrandUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=80)
    logo_url: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip()

    @field_validator("logo_url")
    @classmethod
    def clean_logo_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class BrandOut(BaseModel):
    id: str
    name: str
    logo_url: str | None = None
    created_at: datetime


class CarCreate(BaseModel):
    brand_id: str
    name: str = Field(min_length=2, max_length=120)
    category: CarCategory
    description: str = Field(min_length=10, max_length=2000)
    images: list[str] = Field(default_factory=list)
    daily_rate: float = Field(gt=0)
    seats: int = Field(ge=2, le=9)
    transmission: TransmissionType
    fuel_type: FuelType
    status: str = "active"

    @field_validator("brand_id", "name", "description", mode="before")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("images")
    @classmethod
    def clean_images(cls, value: list[str]) -> list[str]:
        return [image.strip() for image in value if image.strip()]

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        value = value.strip().lower()
        if value not in {"active", "inactive"}:
            raise ValueError("Status must be active or inactive")
        return value


class CarUpdate(BaseModel):
    brand_id: str | None = None
    name: str | None = Field(default=None, min_length=2, max_length=120)
    category: CarCategory | None = None
    description: str | None = Field(default=None, min_length=10, max_length=2000)
    images: list[str] | None = None
    daily_rate: float | None = Field(default=None, gt=0)
    seats: int | None = Field(default=None, ge=2, le=9)
    transmission: TransmissionType | None = None
    fuel_type: FuelType | None = None
    status: str | None = None

    @field_validator("brand_id", "name", "description", mode="before")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip()

    @field_validator("images")
    @classmethod
    def clean_images(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return [image.strip() for image in value if image.strip()]

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip().lower()
        if value not in {"active", "inactive"}:
            raise ValueError("Status must be active or inactive")
        return value


class CarOut(BaseModel):
    id: str
    brand_id: str
    name: str
    category: CarCategory
    description: str
    images: list[str]
    daily_rate: float
    seats: int
    transmission: TransmissionType
    fuel_type: FuelType
    status: str
    created_at: datetime


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
