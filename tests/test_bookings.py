from bson import ObjectId
from fastapi.testclient import TestClient

from app.auth.utils import hash_password
from app.db import get_db
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

    def _matches(self, record: dict, query: dict) -> bool:
        for key, expected in query.items():
            actual = record.get(key)
            if isinstance(expected, dict):
                if "$in" in expected and actual not in expected["$in"]:
                    return False
                if "$lte" in expected and actual > expected["$lte"]:
                    return False
                if "$gte" in expected and actual < expected["$gte"]:
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

    async def update_one(self, query: dict, update: dict):
        record = await self.find_one(query)
        if record and "$set" in update:
            record.update(update["$set"])

    async def delete_one(self, query: dict):
        original_len = len(self.records)
        self.records = [record for record in self.records if not self._matches(record, query)]
        return FakeDeleteResult(original_len - len(self.records))

    async def count_documents(self, query: dict):
        return len([record for record in self.records if self._matches(record, query)])


class FakeDB:
    def __init__(self):
        self.users = FakeCollection()
        self.cars = FakeCollection()
        self.bookings = FakeCollection()
        self.brands = FakeCollection()
        self.enquiries = FakeCollection()
        self.subscribers = FakeCollection()
        self.testimonials = FakeCollection()


def create_client():
    fake_db = FakeDB()

    async def override_get_db():
        return fake_db

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
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


def get_token(client: TestClient) -> str:
    response = client.post(
        "/api/auth/login",
        json={"email": "jane@example.com", "password": "topsecret1"},
    )
    return response.json()["access_token"]


def test_create_booking_and_list_my_bookings():
    client, fake_db = create_client()
    car = seed_car(fake_db)
    seed_user(fake_db)
    token = get_token(client)

    create_response = client.post(
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
    assert body["total_price"] == 150.0

    history_response = client.get(
        "/api/bookings/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert history_response.status_code == 200
    assert len(history_response.json()) == 1


def test_create_booking_rejects_date_conflicts():
    client, fake_db = create_client()
    car = seed_car(fake_db)
    user = seed_user(fake_db)
    token = get_token(client)
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

    response = client.post(
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
