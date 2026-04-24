from datetime import datetime, timezone

from bson import ObjectId
import pytest

from app.auth.utils import hash_password
from tests.test_bookings import FakeDB, create_client


def seed_admin(fake_db: FakeDB) -> dict:
    admin = {
        "_id": ObjectId(),
        "name": "Admin User",
        "email": "admin@example.com",
        "phone": "09000000000",
        "password_hash": hash_password("adminpass1"),
        "is_verified": True,
        "role": "admin",
    }
    fake_db.users.records.append(admin)
    return admin


def get_admin_token(client) -> str:
    return client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "adminpass1"},
    )


@pytest.mark.asyncio
async def test_admin_can_list_and_delete_subscribers():
    client, fake_db = await create_client()
    seed_admin(fake_db)
    subscriber_id = ObjectId()
    fake_db.subscribers.records.append(
        {
            "_id": subscriber_id,
            "email": "hello@example.com",
            "created_at": datetime.now(timezone.utc),
        }
    )
    try:
        login_response = await get_admin_token(client)
        token = login_response.json()["access_token"]

        list_response = await client.get(
            "/api/admin/subscribers",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert list_response.status_code == 200
        assert list_response.json()[0]["email"] == "hello@example.com"

        delete_response = await client.delete(
            f"/api/admin/subscribers/{subscriber_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert delete_response.status_code == 204
        assert fake_db.subscribers.records == []
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_admin_can_mark_enquiry_as_read():
    client, fake_db = await create_client()
    seed_admin(fake_db)
    enquiry_id = ObjectId()
    fake_db.enquiries.records.append(
        {
            "_id": enquiry_id,
            "name": "Ada",
            "email": "ada@example.com",
            "phone": "08012345678",
            "message": "Please tell me if weekend rentals are available.",
            "status": "unread",
            "created_at": datetime.now(timezone.utc),
        }
    )
    try:
        login_response = await get_admin_token(client)
        token = login_response.json()["access_token"]

        response = await client.patch(
            f"/api/admin/enquiries/{enquiry_id}",
            json={"status": "read"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "read"
        assert fake_db.enquiries.records[0]["status"] == "read"
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_admin_can_upsert_site_content():
    client, fake_db = await create_client()
    seed_admin(fake_db)
    try:
        login_response = await get_admin_token(client)
        token = login_response.json()["access_token"]

        create_response = await client.patch(
            "/api/admin/site-content/homepage_hero",
            json={"value": "Drive smarter with Fast Cars"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert create_response.status_code == 200
        assert create_response.json()["key"] == "homepage_hero"
        assert create_response.json()["value"] == "Drive smarter with Fast Cars"

        update_response = await client.patch(
            "/api/admin/site-content/homepage_hero",
            json={"value": "Drive smarter and faster"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert update_response.status_code == 200
        assert len(fake_db.site_content.records) == 1
        assert fake_db.site_content.records[0]["value"] == "Drive smarter and faster"
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_admin_can_list_site_content():
    client, fake_db = await create_client()
    seed_admin(fake_db)
    fake_db.site_content.records.append(
        {
            "_id": ObjectId(),
            "key": "homepage_hero",
            "value": "Drive smarter with Fast Cars",
            "updated_at": datetime.now(timezone.utc),
        }
    )
    try:
        login_response = await get_admin_token(client)
        token = login_response.json()["access_token"]

        response = await client.get(
            "/api/admin/site-content",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()[0]["key"] == "homepage_hero"
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_admin_can_get_user_detail():
    client, fake_db = await create_client()
    seed_admin(fake_db)
    user_id = ObjectId()
    fake_db.users.records.append(
        {
            "_id": user_id,
            "name": "Jane Driver",
            "email": "jane@example.com",
            "phone": "09012345678",
            "password_hash": hash_password("topsecret1"),
            "is_verified": True,
            "role": "user",
        }
    )
    try:
        login_response = await get_admin_token(client)
        token = login_response.json()["access_token"]

        response = await client.get(
            f"/api/admin/users/{user_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["email"] == "jane@example.com"
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_admin_can_list_all_cars_including_inactive_with_brand_name():
    client, fake_db = await create_client()
    seed_admin(fake_db)
    brand_id = ObjectId()
    fake_db.brands.records.append(
        {
            "_id": brand_id,
            "name": "Toyota",
            "logo_url": None,
            "created_at": datetime.now(timezone.utc),
        }
    )
    fake_db.cars.records.append(
        {
            "_id": ObjectId(),
            "brand_id": brand_id,
            "name": "Toyota Corolla",
            "category": "Economy",
            "description": "A reliable sedan for city and airport trips.",
            "images": [],
            "daily_rate": 50.0,
            "seats": 5,
            "transmission": "Automatic",
            "fuel_type": "Petrol",
            "status": "inactive",
            "created_at": datetime.now(timezone.utc),
        }
    )
    try:
        login_response = await get_admin_token(client)
        token = login_response.json()["access_token"]

        response = await client.get(
            "/api/admin/cars/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()[0]["status"] == "inactive"
        assert response.json()[0]["brand_name"] == "Toyota"
    finally:
        await client.aclose()
