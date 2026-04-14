from bson import ObjectId
from fastapi.testclient import TestClient

from app.auth.utils import create_access_token, decode_token, verify_password
from app.db import get_db
from main import app


class FakeInsertResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class FakeUsersCollection:
    def __init__(self):
        self.records = []

    async def find_one(self, query: dict):
        for record in self.records:
            if all(record.get(key) == value for key, value in query.items()):
                return record
        return None

    async def insert_one(self, document: dict):
        stored = document.copy()
        stored["_id"] = ObjectId()
        self.records.append(stored)
        return FakeInsertResult(stored["_id"])

    async def update_one(self, query: dict, update: dict):
        for record in self.records:
            if all(record.get(key) == value for key, value in query.items()):
                if "$set" in update:
                    record.update(update["$set"])
                return


class FakeDB:
    def __init__(self):
        self.users = FakeUsersCollection()


def create_client():
    fake_db = FakeDB()

    async def override_get_db():
        return fake_db

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    return client, fake_db


def teardown_function():
    app.dependency_overrides.clear()


def test_register_returns_token_and_hashes_password():
    client, fake_db = create_client()

    response = client.post(
        "/api/auth/register",
        json={
            "name": "Ada",
            "email": "ADA@example.com",
            "phone": "08000000000",
            "password": "supersecret",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"

    stored_user = fake_db.users.records[0]
    assert stored_user["email"] == "ada@example.com"
    assert stored_user["password_hash"] != "supersecret"
    assert "password" not in stored_user

    payload = decode_token(body["access_token"])
    assert payload["sub"] == str(stored_user["_id"])


def test_login_rejects_invalid_credentials():
    client, _ = create_client()

    response = client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "wrongpass"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_login_and_me_round_trip():
    client, _ = create_client()

    register_response = client.post(
        "/api/auth/register",
        json={
            "name": "Jane Driver",
            "email": "jane@example.com",
            "phone": "09012345678",
            "password": "topsecret1",
        },
    )
    token = register_response.json()["access_token"]

    login_response = client.post(
        "/api/auth/login",
        json={"email": "jane@example.com", "password": "topsecret1"},
    )
    assert login_response.status_code == 200

    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert me_response.status_code == 200
    assert me_response.json() == {
        "_id": me_response.json()["_id"],
        "name": "Jane Driver",
        "email": "jane@example.com",
        "phone": "09012345678",
        "role": "user",
    }


def test_forgot_password_returns_generic_message():
    client, fake_db = create_client()
    fake_db.users.records.append(
        {
            "_id": ObjectId(),
            "name": "Ada",
            "email": "ada@example.com",
            "phone": "08000000000",
            "password_hash": "hashed",
            "role": "user",
        }
    )

    response = client.post(
        "/api/auth/forgot-password",
        json={"email": "ada@example.com"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "If that email is registered, a reset link has been sent"


def test_reset_password_updates_hash():
    client, fake_db = create_client()
    user_id = ObjectId()
    fake_db.users.records.append(
        {
            "_id": user_id,
            "name": "Ada",
            "email": "ada@example.com",
            "phone": "08000000000",
            "password_hash": "old-hash",
            "role": "user",
        }
    )
    token = create_access_token({"sub": str(user_id), "scope": "password_reset"})

    response = client.post(
        "/api/auth/reset-password",
        json={"token": token, "new_password": "newsecret1"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Password reset successful"
    assert verify_password("newsecret1", fake_db.users.records[0]["password_hash"])
