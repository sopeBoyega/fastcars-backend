from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings

client = AsyncIOMotorClient(settings.MONGO_URI)
db = client[settings.MONGO_DB_NAME]

REQUIRED_COLLECTIONS = (
    "users",
    "brands",
    "cars",
    "bookings",
    "testimonials",
    "enquiries",
    "subscribers",
    "site_content",
)


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


async def ensure_database_setup() -> None:
    existing_collections = set(await db.list_collection_names())

    for collection_name in REQUIRED_COLLECTIONS:
        if collection_name not in existing_collections:
            await db.create_collection(collection_name)

    await db.users.create_index("email", unique=True)
    await db.brands.create_index("name", unique=True)
    await db.subscribers.create_index("email", unique=True)
    await db.bookings.create_index(
        [("car_id", 1), ("status", 1), ("start_date", 1), ("end_date", 1)]
    )
    await db.cars.create_index([("brand_id", 1), ("status", 1)])
