import pytest

from tests.test_bookings import create_client


@pytest.mark.asyncio
async def test_newsletter_subscribe_stores_email():
    client, fake_db = await create_client()

    try:
        response = await client.post(
            "/api/newsletter/subscribe",
            json={"email": "driver@example.com"},
        )

        assert response.status_code == 201
        assert response.json()["email"] == "driver@example.com"
        assert len(fake_db.subscribers.records) == 1
        assert fake_db.subscribers.records[0]["email"] == "driver@example.com"
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_newsletter_subscribe_reuses_existing_subscriber_without_duplicates():
    client, fake_db = await create_client()

    try:
        first_response = await client.post(
            "/api/newsletter/subscribe",
            json={"email": "driver@example.com"},
        )
        second_response = await client.post(
            "/api/newsletter/subscribe",
            json={"email": "driver@example.com"},
        )

        assert first_response.status_code == 201
        assert second_response.status_code == 201
        assert len(fake_db.subscribers.records) == 1
    finally:
        await client.aclose()
