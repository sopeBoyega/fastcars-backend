from dataclasses import replace

from app.core import email


def test_send_email_posts_to_brevo(monkeypatch):
    captured: dict = {}

    def fake_post(url, headers, json, timeout):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout

        class FakeResponse:
            def raise_for_status(self):
                return None

        return FakeResponse()

    monkeypatch.setattr(
        email,
        "settings",
        replace(
            email.settings,
            BREVO_API_KEY="xkeysib-test",
            BREVO_SENDER_EMAIL="noreply@example.com",
            BREVO_SENDER_NAME="Fast Cars",
            BREVO_REPLY_TO_EMAIL="support@example.com",
            BREVO_REPLY_TO_NAME="Support Team",
        ),
    )
    monkeypatch.setattr(email.httpx, "post", fake_post)

    email.send_email(
        "Booking confirmed",
        "driver@example.com",
        "Your car is ready.",
        "<p>Your car is ready.</p>",
    )

    assert captured["url"] == email.BREVO_API_URL
    assert captured["headers"]["api-key"] == "xkeysib-test"
    assert captured["headers"]["content-type"] == "application/json"
    assert captured["json"] == {
        "sender": {
            "email": "noreply@example.com",
            "name": "Fast Cars",
        },
        "to": [{"email": "driver@example.com"}],
        "subject": "Booking confirmed",
        "textContent": "Your car is ready.",
        "htmlContent": "<p>Your car is ready.</p>",
        "replyTo": {
            "email": "support@example.com",
            "name": "Support Team",
        },
    }
    assert captured["timeout"] == 10.0


def test_send_email_skips_without_brevo_configuration(monkeypatch):
    called = False

    def fake_post(*args, **kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr(
        email,
        "settings",
        replace(
            email.settings,
            BREVO_API_KEY="your_brevo_api_key",
            BREVO_SENDER_EMAIL="your_verified_sender@example.com",
        ),
    )
    monkeypatch.setattr(email.httpx, "post", fake_post)

    email.send_email("Password reset", "driver@example.com", "Reset link")

    assert called is False
