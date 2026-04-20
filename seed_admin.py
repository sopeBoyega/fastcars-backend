import asyncio
import os
from datetime import datetime, timezone

from app.auth.utils import hash_password
from app.db import db


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def require_setting(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value.strip()


async def seed_admin() -> None:
    email = require_setting("ADMIN_INITIAL_EMAIL", "admin@example.com").lower()
    password = require_setting("ADMIN_INITIAL_PASSWORD", "adminpass1")
    name = require_setting("ADMIN_INITIAL_NAME", "Fast Cars Admin")
    phone = require_setting("ADMIN_INITIAL_PHONE", "09000000000")

    existing = await db.users.find_one({"email": email})
    password_hash = hash_password(password)

    if existing:
        await db.users.update_one(
            {"_id": existing["_id"]},
            {
                "$set": {
                    "name": name,
                    "phone": phone,
                    "role": "admin",
                    "password_hash": password_hash,
                }
            },
        )
        print(f"Updated admin user: {email}")
        return

    await db.users.insert_one(
        {
            "name": name,
            "email": email,
            "phone": phone,
            "password_hash": password_hash,
            "role": "admin",
            "created_at": utcnow(),
        }
    )
    print(f"Created admin user: {email}")


if __name__ == "__main__":
    asyncio.run(seed_admin())
