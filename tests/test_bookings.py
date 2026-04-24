from datetime import date, datetime, time, timezone

from bson import BSON, ObjectId
import pytest
from httpx import ASGITransport, AsyncClient

from app.auth.utils import hash_password
from app.db import get_db
from app.routers.bookings import to_mongo_datetime
from main import app


class FakeInsertResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class FakeDeleteResult:
    def __init__(self, deleted_count: int):
        self.deleted_count = deleted_count


class FakeCursor:
    def __init__(self, records: list[dict]):
        self.records = records

    def sort(self, key: str, direction: int):
        reverse = direction == -1
        self.records = sorted(self.records, key=lambda item: item.get(key), reverse=reverse)
        return self

    async def to_list(self, length: int):
        return self.records[:length]


class FakeCollection:
    def __init__(self):
        self.records: list[dict] = []

    def _normalize_comparison_values(self, actual, expected):
        if isinstance(actual, date) and not isinstance(actual, datetime) and isinstance(expected, datetime):
            actual = datetime.combine(actual, time.min, tzinfo=expected.tzinfo or timezone.utc)
        if isinstance(expected, date) and not isinstance(expected, datetime) and isinstance(actual, datetime):
            expected = datetime.combine(expected, time.min, tzinfo=actual.tzinfo or timezone.utc)
        return actual, expected

    def _matches(self, record: dict, query: dict) -> bool:
        for key, expected in query.items():
            actual = record.get(key)
            if isinstance(expected, dict):
                if "$in" in expected and actual not in expected["$in"]:
                    return False
                if "$ne" in expected and actual == expected["$ne"]:
                    return False
                if "$lte" in expected:
                    actual_cmp, expected_cmp = self._normalize_comparison_values(actual, expected["$lte"])
                    if actual_cmp > expected_cmp:
                        return False
                if "$gte" in expected:
                    actual_cmp, expected_cmp = self._normalize_comparison_values(actual, expected["$gte"])
                    if actual_cmp < expected_cmp:
                        return False
            elif actual != expected:
                return False
        return True

    async def find_one(self, query: dict):
        for record in self.records:
            if self._matches(record, query):
                return record
        return None

    def find(self, query: dict):
        return FakeCursor([record for record in self.records if self._matches(record, query)])

    async def insert_one(self, document: dict):
        stored = document.copy()
        stored["_id"] = ObjectId()
        self.records.append(stored)
        return FakeInsertResult(stored["_id"])

    async def update_one(self, query: dict, update: dict, upsert: bool = False):
        record = await self.find_one(query)
        if record and "$set" in update:
            record.update(update["$set"])
            return
        if record is None and upsert:
            stored = query.copy()
            if "$set" in update:
                stored.update(update["$set"])
            stored["_id"] = ObjectId()
            self.records.append(stored)

    async def delete_one(self, query: dict):
        original_len = len(self.records)
        self.records = [record for record in self.records if not self._matches(record, query)]
        return FakeDeleteResult(original_len - len(self.records))

    async def count_documents(self, query: dict):
        return len([record for record in self.records if self._matches(record, query)])


class FakeDB:
    def __init__(self):
        self.users = FakeCollection()
        self.pending_registrations = FakeCollection()
        self.cars = FakeCollection()
        self.bookings = FakeCollection()
        self.brands = FakeCollection()
        self.enquiries = FakeCollection()
        self.subscribers = FakeCollection()
        self.testimonials = FakeCollection()
        self.site_content = FakeCollection()


async def create_client():
    fake_db = FakeDB()

    async def override_get_db():
        return fake_db

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://testserver")
    return client, fake_db


def teardown_function():
    app.dependency_overrides.clear()


def seed_user(fake_db: FakeDB) -> dict:
    user = {
        "_id": ObjectId(),
        "name": "Jane Driver",
        "email": "jane@example.com",
        "phone": "09012345678",
        "password_hash": hash_password("topsecret1"),
        "is_verified": True,
        "role": "user",
    }
    fake_db.users.records.append(user)
    return user


def seed_car(fake_db: FakeDB) -> dict:
    car = {
        "_id": ObjectId(),
        "brand_id": ObjectId(),
        "name": "Toyota Corolla",
        "category": "Economy",
        "description": "A reliable sedan for city and airport trips.",
        "images": [],
        "daily_rate": 50.0,
        "seats": 5,
        "transmission": "Automatic",
        "fuel_type": "Petrol",
        "status": "active",
        "created_at": "2026-04-13T00:00:00Z",
    }
    fake_db.cars.records.append(car)
    return car


async def get_token(client: AsyncClient) -> str:
    response = await client.post(
        "/api/auth/login",
        json={"email": "jane@example.com", "password": "topsecret1"},
    )
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_create_booking_and_list_my_bookings():
    client, fake_db = await create_client()
    car = seed_car(fake_db)
    seed_user(fake_db)
    token = await get_token(client)

    try:
        create_response = await client.post(
            "/api/bookings/",
            json={
                "car_id": str(car["_id"]),
                "start_date": "2026-04-15",
                "end_date": "2026-04-17",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert create_response.status_code == 201
        body = create_response.json()
        assert body["status"] == "pending"
        assert body["total_days"] == 3
        assert body["total_cost"] == 150.0
        assert body["car_name"] == "Toyota Corolla"
        assert "booking_ref" in body
        assert isinstance(fake_db.bookings.records[0]["start_date"], datetime)
        assert isinstance(fake_db.bookings.records[0]["end_date"], datetime)

        history_response = await client.get(
            "/api/bookings/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert history_response.status_code == 200
        assert len(history_response.json()) == 1
        assert history_response.json()[0]["car_name"] == "Toyota Corolla"
    finally:
        await client.aclose()


def test_booking_dates_are_bson_encodable():
    document = {
        "start_date": to_mongo_datetime(__import__("datetime").date(2026, 4, 23)),
        "end_date": to_mongo_datetime(__import__("datetime").date(2026, 4, 25)),
    }

    encoded = BSON.encode(document)

    assert encoded


@pytest.mark.asyncio
async def test_create_booking_rejects_date_conflicts():
    client, fake_db = await create_client()
    car = seed_car(fake_db)
    user = seed_user(fake_db)
    token = await get_token(client)
    fake_db.bookings.records.append(
        {
            "_id": ObjectId(),
            "user_id": user["_id"],
            "car_id": car["_id"],
            "start_date": __import__("datetime").date(2026, 4, 20),
            "end_date": __import__("datetime").date(2026, 4, 22),
            "total_days": 3,
            "total_price": 150.0,
            "status": "confirmed",
            "created_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        }
    )

    try:
        response = await client.post(
            "/api/bookings/",
            json={
                "car_id": str(car["_id"]),
                "start_date": "2026-04-21",
                "end_date": "2026-04-23",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 409
        assert response.json()["detail"] == "Car is already booked for the selected dates"
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_admin_booking_list_and_detail_include_friendly_fields():
    client, fake_db = await create_client()
    car = seed_car(fake_db)
    user = seed_user(fake_db)
    admin = {
        "_id": ObjectId(),
        "name": "Admin User",
        "email": "admin@example.com",
        "phone": "09000000000",
        "password_hash": hash_password("adminpass1"),
        "role": "admin",
    }
    fake_db.users.records.append(admin)
    booking_id = ObjectId()
    fake_db.bookings.records.append(
        {
            "_id": booking_id,
            "user_id": user["_id"],
            "car_id": car["_id"],
            "start_date": __import__("datetime").date(2026, 4, 20),
            "end_date": __import__("datetime").date(2026, 4, 22),
            "total_days": 3,
            "total_price": 150.0,
            "status": "confirmed",
            "created_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        }
    )

    try:
        login_response = await client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "adminpass1"},
        )
        token = login_response.json()["access_token"]

        list_response = await client.get(
            "/api/admin/bookings/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert list_response.status_code == 200
        assert list_response.json()[0]["customer"] == "Jane Driver"
        assert list_response.json()[0]["user_email"] == "jane@example.com"
        assert list_response.json()[0]["car_name"] == "Toyota Corolla"
        assert list_response.json()[0]["total_cost"] == 150.0

        detail_response = await client.get(
            f"/api/admin/bookings/{booking_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert detail_response.status_code == 200
        assert detail_response.json()["car_name"] == "Toyota Corolla"
        assert detail_response.json()["customer"] == "Jane Driver"
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_admin_booking_status_updates_return_enriched_booking_shape():
    client, fake_db = await create_client()
    car = seed_car(fake_db)
    user = seed_user(fake_db)
    admin = {
        "_id": ObjectId(),
        "name": "Admin User",
        "email": "admin@example.com",
        "phone": "09000000000",
        "password_hash": hash_password("adminpass1"),
        "role": "admin",
    }
    fake_db.users.records.append(admin)
    booking_id = ObjectId()
    fake_db.bookings.records.append(
        {
            "_id": booking_id,
            "user_id": user["_id"],
            "car_id": car["_id"],
            "start_date": __import__("datetime").date(2026, 4, 20),
            "end_date": __import__("datetime").date(2026, 4, 22),
            "total_days": 3,
            "total_price": 150.0,
            "status": "pending",
            "created_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        }
    )

    try:
        login_response = await client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "adminpass1"},
        )
        token = login_response.json()["access_token"]

        confirm_response = await client.patch(
            f"/api/admin/bookings/{booking_id}/confirm",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert confirm_response.status_code == 200
        assert confirm_response.json()["status"] == "confirmed"
        assert confirm_response.json()["customer"] == "Jane Driver"
        assert confirm_response.json()["car_name"] == "Toyota Corolla"
        assert confirm_response.json()["total_cost"] == 150.0

        cancel_response = await client.patch(
            f"/api/admin/bookings/{booking_id}/cancel",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert cancel_response.status_code == 200
        assert cancel_response.json()["status"] == "cancelled"
        assert cancel_response.json()["customer"] == "Jane Driver"
        assert cancel_response.json()["car_name"] == "Toyota Corolla"
    finally:
        await client.aclose()
