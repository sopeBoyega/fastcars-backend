from datetime import timedelta

from bson import ObjectId
import pytest

from app.auth.utils import create_access_token, decode_token, hash_password, verify_password
from app.db import utcnow
from app.routers import auth as auth_router
from tests.test_bookings import create_client


@pytest.mark.asyncio
async def test_register_creates_pending_registration_and_hashes_secrets(monkeypatch):
    client, fake_db = await create_client()
    monkeypatch.setattr(auth_router, "generate_otp", lambda: "123456")

    try:
        response = await client.post(
            "/api/auth/register",
            json={
                "name": "Ada",
                "email": "ADA@example.com",
                "phone": "08000000000",
                "password": "supersecret",
            },
        )

        assert response.status_code == 201
        assert response.json() == {
            "message": "Verification code sent to your email",
            "email": "ada@example.com",
            "expires_in_minutes": auth_router.settings.REGISTRATION_OTP_EXPIRE_MINUTES,
        }
        assert fake_db.users.records == []
        assert len(fake_db.pending_registrations.records) == 1

        pending = fake_db.pending_registrations.records[0]
        assert pending["email"] == "ada@example.com"
        assert pending["password_hash"] != "supersecret"
        assert verify_password("supersecret", pending["password_hash"])
        assert verify_password("123456", pending["otp_hash"])
        assert "password" not in pending
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_verify_registration_otp_creates_user_and_returns_token(monkeypatch):
    client, fake_db = await create_client()
    monkeypatch.setattr(auth_router, "generate_otp", lambda: "123456")

    try:
        register_response = await client.post(
            "/api/auth/register",
            json={
                "name": "Jane Driver",
                "email": "jane@example.com",
                "phone": "09012345678",
                "password": "topsecret1",
            },
        )
        assert register_response.status_code == 201

        verify_response = await client.post(
            "/api/auth/register/verify-otp",
            json={"email": "jane@example.com", "otp": "123456"},
        )

        assert verify_response.status_code == 200
        body = verify_response.json()
        assert body["token_type"] == "bearer"
        assert len(fake_db.users.records) == 1
        assert fake_db.pending_registrations.records == []

        stored_user = fake_db.users.records[0]
        assert stored_user["email"] == "jane@example.com"
        assert stored_user["is_verified"] is True
        assert verify_password("topsecret1", stored_user["password_hash"])

        payload = decode_token(body["access_token"])
        assert payload["sub"] == str(stored_user["_id"])
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_login_rejects_unverified_registration(monkeypatch):
    client, _ = await create_client()
    monkeypatch.setattr(auth_router, "generate_otp", lambda: "123456")

    try:
        await client.post(
            "/api/auth/register",
            json={
                "name": "Ada",
                "email": "ada@example.com",
                "phone": "08000000000",
                "password": "supersecret",
            },
        )

        response = await client.post(
            "/api/auth/login",
            json={"email": "ada@example.com", "password": "supersecret"},
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "Please verify your email before logging in"
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_resend_registration_otp_refreshes_pending_code(monkeypatch):
    client, fake_db = await create_client()
    monkeypatch.setattr(auth_router, "generate_otp", lambda: "123456")

    try:
        await client.post(
            "/api/auth/register",
            json={
                "name": "Ada",
                "email": "ada@example.com",
                "phone": "08000000000",
                "password": "supersecret",
            },
        )
        fake_db.pending_registrations.records[0]["attempt_count"] = 2
        first_hash = fake_db.pending_registrations.records[0]["otp_hash"]

        monkeypatch.setattr(auth_router, "generate_otp", lambda: "654321")
        response = await client.post(
            "/api/auth/register/resend-otp",
            json={"email": "ada@example.com"},
        )

        assert response.status_code == 200
        pending = fake_db.pending_registrations.records[0]
        assert pending["otp_hash"] != first_hash
        assert verify_password("654321", pending["otp_hash"])
        assert pending["attempt_count"] == 0
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_login_and_me_round_trip_for_verified_user():
    client, fake_db = await create_client()
    fake_db.users.records.append(
        {
            "_id": ObjectId(),
            "name": "Jane Driver",
            "email": "jane@example.com",
            "phone": "09012345678",
            "password_hash": hash_password("topsecret1"),
            "is_verified": True,
            "role": "user",
        }
    )

    try:
        login_response = await client.post(
            "/api/auth/login",
            json={"email": "jane@example.com", "password": "topsecret1"},
        )
        token = login_response.json()["access_token"]

        me_response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert login_response.status_code == 200
        assert me_response.status_code == 200
        assert me_response.json() == {
            "_id": me_response.json()["_id"],
            "name": "Jane Driver",
            "email": "jane@example.com",
            "phone": "09012345678",
            "role": "user",
        }
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_forgot_password_returns_generic_message():
    client, fake_db = await create_client()
    fake_db.users.records.append(
        {
            "_id": ObjectId(),
            "name": "Ada",
            "email": "ada@example.com",
            "phone": "08000000000",
            "password_hash": "hashed",
            "is_verified": True,
            "role": "user",
        }
    )

    try:
        response = await client.post(
            "/api/auth/forgot-password",
            json={"email": "ada@example.com"},
        )

        assert response.status_code == 200
        assert response.json()["message"] == "If that email is registered, a reset link has been sent"
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_reset_password_updates_hash():
    client, fake_db = await create_client()
    user_id = ObjectId()
    fake_db.users.records.append(
        {
            "_id": user_id,
            "name": "Ada",
            "email": "ada@example.com",
            "phone": "08000000000",
            "password_hash": "old-hash",
            "is_verified": True,
            "role": "user",
        }
    )
    token = create_access_token({"sub": str(user_id), "scope": "password_reset"})

    try:
        response = await client.post(
            "/api/auth/reset-password",
            json={"token": token, "new_password": "newsecret1"},
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Password reset successful"
        assert verify_password("newsecret1", fake_db.users.records[0]["password_hash"])
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_verify_registration_otp_rejects_expired_codes():
    client, fake_db = await create_client()
    fake_db.pending_registrations.records.append(
        {
            "_id": ObjectId(),
            "name": "Ada",
            "email": "ada@example.com",
            "phone": "08000000000",
            "password_hash": hash_password("supersecret"),
            "otp_hash": hash_password("123456"),
            "attempt_count": 0,
            "created_at": utcnow() - timedelta(minutes=30),
            "otp_sent_at": utcnow() - timedelta(minutes=30),
            "expires_at": utcnow() - timedelta(minutes=20),
        }
    )

    try:
        response = await client.post(
            "/api/auth/register/verify-otp",
            json={"email": "ada@example.com", "otp": "123456"},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "OTP has expired. Request a new code."
        assert fake_db.pending_registrations.records == []
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_verify_registration_otp_handles_naive_mongo_datetimes():
    client, fake_db = await create_client()
    fake_db.pending_registrations.records.append(
        {
            "_id": ObjectId(),
            "name": "Ada",
            "email": "ada@example.com",
            "phone": "08000000000",
            "password_hash": hash_password("supersecret"),
            "otp_hash": hash_password("123456"),
            "attempt_count": 0,
            "created_at": utcnow().replace(tzinfo=None),
            "otp_sent_at": utcnow().replace(tzinfo=None),
            "expires_at": (utcnow() + timedelta(minutes=5)).replace(tzinfo=None),
        }
    )

    try:
        response = await client.post(
            "/api/auth/register/verify-otp",
            json={"email": "ada@example.com", "otp": "123456"},
        )

        assert response.status_code == 200
        assert response.json()["token_type"] == "bearer"
        assert len(fake_db.users.records) == 1
        assert fake_db.users.records[0]["created_at"].tzinfo is not None
    finally:
        await client.aclose()
