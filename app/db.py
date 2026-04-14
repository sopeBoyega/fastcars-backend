from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings

client = AsyncIOMotorClient(settings.MONGO_URI)
db = client[settings.MONGO_DB_NAME]


async def get_db():
    return db


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def parse_object_id(value: str, field_name: str = "id") -> ObjectId:
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        raise ValueError(f"Invalid {field_name}")


def stringify_id(document: dict | None) -> dict | None:
    if document is None:
        return None

    data = document.copy()
    if "_id" in data:
        data["_id"] = str(data["_id"])
    return data
