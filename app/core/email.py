from fastapi import BackgroundTasks

from app.core.config import settings


def send_email(subject: str, to_email: str, body: str) -> None:
    if not settings.EMAIL_USER or not settings.EMAIL_PASSWORD:
        return
    if settings.EMAIL_PASSWORD == "your_gmail_app_password":
        return

    try:
        import yagmail

        yag = yagmail.SMTP(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
        yag.send(to=to_email, subject=subject, contents=body)
    except Exception:
        return


def queue_email(
    background_tasks: BackgroundTasks,
    *,
    subject: str,
    to_email: str,
    body: str,
) -> None:
    background_tasks.add_task(send_email, subject, to_email, body)
