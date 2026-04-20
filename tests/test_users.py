import pytest

from app.auth.utils import verify_password
from tests.test_bookings import create_client, seed_user


@pytest.mark.asyncio
async def test_update_my_profile():
    client, fake_db = await create_client()
    seed_user(fake_db)
    try:
        login_response = await client.post(
            "/api/auth/login",
            json={"email": "jane@example.com", "password": "topsecret1"},
        )
        token = login_response.json()["access_token"]

        response = await client.patch(
            "/api/users/me",
            json={"name": "Jane Rider", "phone": "08123456789"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Jane Rider"
        assert response.json()["phone"] == "08123456789"
        assert fake_db.users.records[0]["name"] == "Jane Rider"
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_change_my_password():
    client, fake_db = await create_client()
    seed_user(fake_db)
    try:
        login_response = await client.post(
            "/api/auth/login",
            json={"email": "jane@example.com", "password": "topsecret1"},
        )
        token = login_response.json()["access_token"]

        response = await client.patch(
            "/api/users/me/password",
            json={"current_password": "topsecret1", "new_password": "evenbetter9"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Password updated successfully"
        assert verify_password("evenbetter9", fake_db.users.records[0]["password_hash"])
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_change_my_password_rejects_wrong_current_password():
    client, fake_db = await create_client()
    seed_user(fake_db)
    try:
        login_response = await client.post(
            "/api/auth/login",
            json={"email": "jane@example.com", "password": "topsecret1"},
        )
        token = login_response.json()["access_token"]

        response = await client.patch(
            "/api/users/me/password",
            json={"current_password": "wrongpass1", "new_password": "evenbetter9"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Current password is incorrect"
    finally:
        await client.aclose()
