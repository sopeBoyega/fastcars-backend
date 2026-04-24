import logging
from dataclasses import dataclass
from html import escape

import httpx
from fastapi import BackgroundTasks

from app.core.config import settings

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"
PLACEHOLDER_VALUES = {
    "your_brevo_api_key",
    "your_verified_sender@example.com",
}
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EmailContent:
    text: str
    html: str


def is_brevo_configured() -> bool:
    if not settings.BREVO_API_KEY or not settings.BREVO_SENDER_EMAIL:
        return False
    return (
        settings.BREVO_API_KEY not in PLACEHOLDER_VALUES
        and settings.BREVO_SENDER_EMAIL not in PLACEHOLDER_VALUES
    )


def _normalize_paragraphs(paragraphs: list[str]) -> list[str]:
    return [paragraph.strip() for paragraph in paragraphs if paragraph and paragraph.strip()]


def render_email_template(
    *,
    preheader: str,
    title: str,
    intro: str,
    paragraphs: list[str] | None = None,
    details: list[tuple[str, str]] | None = None,
    highlight_label: str | None = None,
    highlight_value: str | None = None,
    cta_label: str | None = None,
    cta_url: str | None = None,
    footer_note: str | None = None,
) -> EmailContent:
    body_paragraphs = _normalize_paragraphs(paragraphs or [])
    detail_rows = [(label.strip(), value.strip()) for label, value in (details or []) if label and value]

    text_lines = [title, "", intro]
    if body_paragraphs:
        text_lines.extend(["", *body_paragraphs])
    if highlight_label and highlight_value:
        text_lines.extend(["", f"{highlight_label}: {highlight_value}"])
    if detail_rows:
        text_lines.append("")
        text_lines.extend(f"{label}: {value}" for label, value in detail_rows)
    if cta_label and cta_url:
        text_lines.extend(["", f"{cta_label}: {cta_url}"])
    if footer_note:
        text_lines.extend(["", footer_note])
    text_lines.extend(["", "Fast Cars"])

    detail_rows_html = "".join(
        f"""
        <tr>
          <td style="padding: 12px 0; color: #6b7280; font-size: 13px; width: 38%;">{escape(label)}</td>
          <td style="padding: 12px 0; color: #111827; font-size: 14px; font-weight: 600;">{escape(value)}</td>
        </tr>
        """
        for label, value in detail_rows
    )
    details_section_html = ""
    if detail_rows_html:
        details_section_html = f"""
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-top: 24px; border-top: 1px solid #e5e7eb; border-bottom: 1px solid #e5e7eb;">
          {detail_rows_html}
        </table>
        """

    highlight_section_html = ""
    if highlight_label and highlight_value:
        highlight_section_html = f"""
        <div style="margin-top: 24px; border-radius: 18px; background: linear-gradient(135deg, #111827 0%, #1f2937 100%); padding: 20px; text-align: center;">
          <div style="color: #fbbf24; font-size: 12px; letter-spacing: 0.2em; text-transform: uppercase;">{escape(highlight_label)}</div>
          <div style="margin-top: 8px; color: #ffffff; font-size: 32px; font-weight: 800; letter-spacing: 0.28em;">{escape(highlight_value)}</div>
        </div>
        """

    cta_section_html = ""
    if cta_label and cta_url:
        cta_section_html = f"""
        <div style="margin-top: 28px;">
          <a href="{escape(cta_url, quote=True)}" style="display: inline-block; border-radius: 999px; background: linear-gradient(135deg, #f97316 0%, #fbbf24 100%); color: #111827; font-size: 14px; font-weight: 700; text-decoration: none; padding: 14px 24px;">
            {escape(cta_label)}
          </a>
        </div>
        """

    paragraph_html = "".join(
        f'<p style="margin: 16px 0 0; color: #374151; font-size: 15px; line-height: 1.7;">{escape(paragraph)}</p>'
        for paragraph in body_paragraphs
    )
    footer_note_html = ""
    if footer_note:
        footer_note_html = (
            f'<p style="margin: 24px 0 0; color: #6b7280; font-size: 13px; line-height: 1.7;">{escape(footer_note)}</p>'
        )

    html = f"""\
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{escape(title)}</title>
  </head>
  <body style="margin: 0; padding: 0; background: #f3f4f6; font-family: Arial, Helvetica, sans-serif;">
    <div style="display: none; max-height: 0; overflow: hidden; opacity: 0;">{escape(preheader)}</div>
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background: #f3f4f6; padding: 24px 12px;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 640px;">
            <tr>
              <td style="padding-bottom: 16px; text-align: center;">
                <div style="display: inline-block; border-radius: 999px; background: #111827; color: #f9fafb; padding: 10px 18px; font-size: 12px; font-weight: 700; letter-spacing: 0.24em;">
                  FAST CARS
                </div>
              </td>
            </tr>
            <tr>
              <td style="border-radius: 28px; background: #ffffff; padding: 36px 32px; box-shadow: 0 20px 45px rgba(17, 24, 39, 0.08);">
                <div style="display: inline-block; border-radius: 999px; background: #fff7ed; color: #c2410c; padding: 8px 12px; font-size: 12px; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase;">
                  Customer Update
                </div>
                <h1 style="margin: 20px 0 0; color: #111827; font-size: 30px; line-height: 1.2;">{escape(title)}</h1>
                <p style="margin: 18px 0 0; color: #374151; font-size: 15px; line-height: 1.7;">{escape(intro)}</p>
                {paragraph_html}
                {highlight_section_html}
                {details_section_html}
                {cta_section_html}
                {footer_note_html}
              </td>
            </tr>
            <tr>
              <td style="padding: 18px 8px 0; text-align: center; color: #6b7280; font-size: 12px; line-height: 1.7;">
                Fast Cars keeps your rentals, bookings, and updates moving smoothly.
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""
    return EmailContent(text="\n".join(text_lines), html=html)


def build_registration_otp_email(name: str, otp: str, expires_in_minutes: int) -> EmailContent:
    return render_email_template(
        preheader="Use this one-time code to finish creating your Fast Cars account.",
        title="Confirm your email address",
        intro=f"Hi {name}, welcome to Fast Cars. Enter the code below to verify your email and finish creating your account.",
        paragraphs=[
            f"This verification code expires in {expires_in_minutes} minutes.",
            "If you did not start this sign-up, you can safely ignore this email.",
        ],
        highlight_label="Your OTP",
        highlight_value=otp,
        footer_note="For your security, never share this code with anyone.",
    )


def build_password_reset_email(name: str, reset_url: str) -> EmailContent:
    return render_email_template(
        preheader="Reset your Fast Cars password securely.",
        title="Reset your password",
        intro=f"Hi {name}, we received a request to reset your Fast Cars password.",
        paragraphs=[
            "Use the button below to choose a new password.",
            "If you did not request this, you can ignore this email and your current password will remain unchanged.",
        ],
        cta_label="Reset Password",
        cta_url=reset_url,
        footer_note="Password reset links expire automatically for your protection.",
    )


def build_booking_received_email(
    *,
    name: str,
    car_name: str,
    start_date: str,
    end_date: str,
    total_price: str,
) -> EmailContent:
    return render_email_template(
        preheader="Your booking request is in and pending confirmation.",
        title="Booking request received",
        intro=f"Hi {name}, we have received your booking request for {car_name}.",
        paragraphs=[
            "Our team will review the request and confirm availability shortly.",
        ],
        details=[
            ("Vehicle", car_name),
            ("Pick-up date", start_date),
            ("Return date", end_date),
            ("Estimated total", total_price),
        ],
        footer_note="We will email you again as soon as the booking is confirmed.",
    )


def build_booking_confirmed_email(
    *,
    name: str,
    car_name: str,
    start_date: str,
    end_date: str,
) -> EmailContent:
    return render_email_template(
        preheader="Your Fast Cars booking is confirmed.",
        title="Your booking is confirmed",
        intro=f"Hi {name}, your booking for {car_name} is now confirmed.",
        paragraphs=[
            "We are looking forward to getting you on the road.",
        ],
        details=[
            ("Vehicle", car_name),
            ("Pick-up date", start_date),
            ("Return date", end_date),
        ],
        footer_note="If you need to make a change, reply to this email and our team will help.",
    )


def build_subscription_confirmation_email(email_address: str) -> EmailContent:
    return render_email_template(
        preheader="You are now subscribed to Fast Cars updates.",
        title="Thanks for subscribing",
        intro="You are officially on the Fast Cars newsletter list.",
        paragraphs=[
            "We will send you occasional updates on new arrivals, rental offers, and important service updates.",
        ],
        details=[("Subscribed email", email_address)],
        footer_note="You can contact us any time if you want to update your subscription details.",
    )


def build_admin_enquiry_email(
    *,
    name: str,
    email_address: str,
    phone: str | None,
    message: str,
) -> EmailContent:
    details = [("Customer", name), ("Email", email_address)]
    if phone:
        details.append(("Phone", phone))
    return render_email_template(
        preheader="A new enquiry just came in from the Fast Cars website.",
        title="New customer enquiry",
        intro=f"{name} sent a new enquiry from the website.",
        paragraphs=[message],
        details=details,
        footer_note="Log in to the admin dashboard to review and respond.",
    )


def build_admin_subscription_email(email_address: str) -> EmailContent:
    return render_email_template(
        preheader="A new newsletter subscriber has been captured.",
        title="New newsletter subscriber",
        intro="A customer just joined the Fast Cars mailing list.",
        details=[("Subscriber email", email_address)],
        footer_note="You can review the full subscriber list in the admin dashboard.",
    )


def send_email(subject: str, to_email: str | None, body: str, html_body: str | None = None) -> None:
    if not to_email or not is_brevo_configured():
        return

    payload = {
        "sender": {
            "email": settings.BREVO_SENDER_EMAIL,
            "name": settings.BREVO_SENDER_NAME,
        },
        "to": [{"email": to_email}],
        "subject": subject,
        "textContent": body,
    }
    if html_body:
        payload["htmlContent"] = html_body
    if settings.BREVO_REPLY_TO_EMAIL:
        payload["replyTo"] = {
            "email": settings.BREVO_REPLY_TO_EMAIL,
            "name": settings.BREVO_REPLY_TO_NAME or settings.BREVO_SENDER_NAME,
        }

    try:
        response = httpx.post(
            BREVO_API_URL,
            headers={
                "accept": "application/json",
                "api-key": settings.BREVO_API_KEY,
                "content-type": "application/json",
            },
            json=payload,
            timeout=10.0,
        )
        response.raise_for_status()
    except httpx.HTTPError:
        logger.exception("Failed to send email via Brevo")
        return


def queue_email(
    background_tasks: BackgroundTasks,
    *,
    subject: str,
    to_email: str | None,
    body: str,
    html_body: str | None = None,
) -> None:
    background_tasks.add_task(send_email, subject, to_email, body, html_body)
