import asyncio
from datetime import datetime, timezone

from app.db import db


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


BRANDS = [
    {"name": "Toyota", "logo_url": "https://images.unsplash.com/photo-1619767886558-efdc259cde1a"},
    {"name": "Honda", "logo_url": "https://images.unsplash.com/photo-1552519507-da3b142c6e3d"},
    {"name": "Mercedes-Benz", "logo_url": "https://images.unsplash.com/photo-1503376780353-7e6692767b70"},
    {"name": "BMW", "logo_url": "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7"},
    {"name": "Lexus", "logo_url": "https://images.unsplash.com/photo-1549399542-7e3f8b79c341"},
    {"name": "Ford", "logo_url": "https://images.unsplash.com/photo-1494976388531-d1058494cdd8"},
]


CARS = [
    {
        "brand_name": "Toyota",
        "name": "Toyota Corolla",
        "category": "Economy",
        "description": "Fuel-efficient compact sedan ideal for city rides, work trips, and affordable daily rentals.",
        "images": ["https://images.unsplash.com/photo-1549399542-7e3f8b79c341"],
        "daily_rate": 45.0,
        "seats": 5,
        "transmission": "Automatic",
        "fuel_type": "Petrol",
        "status": "active",
    },
    {
        "brand_name": "Toyota",
        "name": "Toyota RAV4",
        "category": "SUV",
        "description": "Comfortable family SUV with generous cabin space and smooth handling for longer road trips.",
        "images": ["https://images.unsplash.com/photo-1511919884226-fd3cad34687c"],
        "daily_rate": 80.0,
        "seats": 5,
        "transmission": "Automatic",
        "fuel_type": "Hybrid",
        "status": "active",
    },
    {
        "brand_name": "Honda",
        "name": "Honda Civic",
        "category": "Economy",
        "description": "Reliable and stylish compact car suited for daily commuting and efficient personal travel.",
        "images": ["https://images.unsplash.com/photo-1552519507-da3b142c6e3d"],
        "daily_rate": 48.0,
        "seats": 5,
        "transmission": "Automatic",
        "fuel_type": "Petrol",
        "status": "active",
    },
    {
        "brand_name": "Honda",
        "name": "Honda CR-V",
        "category": "SUV",
        "description": "Versatile midsize SUV with solid boot space and a comfortable ride for family bookings.",
        "images": ["https://images.unsplash.com/photo-1502877338535-766e1452684a"],
        "daily_rate": 82.0,
        "seats": 5,
        "transmission": "Automatic",
        "fuel_type": "Petrol",
        "status": "active",
    },
    {
        "brand_name": "Mercedes-Benz",
        "name": "Mercedes-Benz C300",
        "category": "Premium",
        "description": "Premium executive sedan with a refined interior, ideal for business and VIP pickups.",
        "images": ["https://images.unsplash.com/photo-1503376780353-7e6692767b70"],
        "daily_rate": 120.0,
        "seats": 5,
        "transmission": "Automatic",
        "fuel_type": "Petrol",
        "status": "active",
    },
    {
        "brand_name": "Mercedes-Benz",
        "name": "Mercedes-Benz GLE 350",
        "category": "Luxury",
        "description": "Luxury SUV offering premium comfort, elevated styling, and excellent long-distance performance.",
        "images": ["https://images.unsplash.com/photo-1519641471654-76ce0107ad1b"],
        "daily_rate": 180.0,
        "seats": 5,
        "transmission": "Automatic",
        "fuel_type": "Diesel",
        "status": "active",
    },
    {
        "brand_name": "BMW",
        "name": "BMW 3 Series",
        "category": "Premium",
        "description": "Sporty premium sedan with responsive handling and a polished interior for upscale trips.",
        "images": ["https://images.unsplash.com/photo-1492144534655-ae79c964c9d7"],
        "daily_rate": 125.0,
        "seats": 5,
        "transmission": "Automatic",
        "fuel_type": "Petrol",
        "status": "active",
    },
    {
        "brand_name": "Lexus",
        "name": "Lexus RX 350",
        "category": "Luxury",
        "description": "Quiet and refined luxury SUV well suited for corporate travel and airport transfers.",
        "images": ["https://images.unsplash.com/photo-1549399542-7e3f8b79c341"],
        "daily_rate": 170.0,
        "seats": 5,
        "transmission": "Automatic",
        "fuel_type": "Hybrid",
        "status": "active",
    },
    {
        "brand_name": "Ford",
        "name": "Ford Explorer",
        "category": "SUV",
        "description": "Spacious SUV with three-row seating, good for group outings and family vacations.",
        "images": ["https://images.unsplash.com/photo-1502877338535-766e1452684a"],
        "daily_rate": 95.0,
        "seats": 7,
        "transmission": "Automatic",
        "fuel_type": "Petrol",
        "status": "active",
    },
    {
        "brand_name": "BMW",
        "name": "BMW i4",
        "category": "Luxury",
        "description": "Modern electric grand coupe with premium styling and a smooth, quiet driving experience.",
        "images": ["https://images.unsplash.com/photo-1617531653332-bd46c24f2068"],
        "daily_rate": 190.0,
        "seats": 5,
        "transmission": "Automatic",
        "fuel_type": "Electric",
        "status": "active",
    },
]


async def ensure_brand_ids() -> dict[str, object]:
    brand_ids: dict[str, object] = {}

    for brand in BRANDS:
        existing = await db.brands.find_one({"name": brand["name"]})
        if existing:
            brand_ids[brand["name"]] = existing["_id"]
            continue

        payload = {**brand, "created_at": utcnow()}
        result = await db.brands.insert_one(payload)
        brand_ids[brand["name"]] = result.inserted_id

    return brand_ids


async def seed_cars() -> None:
    brand_ids = await ensure_brand_ids()
    inserted = 0
    skipped = 0

    for car in CARS:
        existing = await db.cars.find_one({"name": car["name"]})
        if existing:
            skipped += 1
            continue

        payload = {
            "brand_id": brand_ids[car["brand_name"]],
            "name": car["name"],
            "category": car["category"],
            "description": car["description"],
            "images": car["images"],
            "daily_rate": car["daily_rate"],
            "seats": car["seats"],
            "transmission": car["transmission"],
            "fuel_type": car["fuel_type"],
            "status": car["status"],
            "created_at": utcnow(),
        }
        await db.cars.insert_one(payload)
        inserted += 1

    print(f"Cars inserted: {inserted}")
    print(f"Cars skipped: {skipped}")


if __name__ == "__main__":
    asyncio.run(seed_cars())
