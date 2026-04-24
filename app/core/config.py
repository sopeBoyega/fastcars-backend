import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def optional_env(*names: str, default: str | None = None) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return default


@dataclass(frozen=True)
class Settings:
    MONGO_URI: str
    SECRET_KEY: str
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str
    MONGO_DB_NAME: str = "fastcars_db"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080
    REGISTRATION_OTP_EXPIRE_MINUTES: int = 10
    REGISTRATION_OTP_LENGTH: int = 6
    REGISTRATION_OTP_MAX_ATTEMPTS: int = 5
    FRONTEND_URL: str = "http://localhost:8501"
    JWT_ALGORITHM: str = "HS256"
    BREVO_API_KEY: str | None = None
    BREVO_SENDER_EMAIL: str | None = None
    BREVO_SENDER_NAME: str = "Fast Cars"
    BREVO_REPLY_TO_EMAIL: str | None = None
    BREVO_REPLY_TO_NAME: str | None = None
    ADMIN_NOTIFICATION_EMAIL: str | None = None


settings = Settings(
    MONGO_URI=require_env("MONGO_URI"),
    SECRET_KEY=require_env("SECRET_KEY"),
    CLOUDINARY_CLOUD_NAME=require_env("CLOUDINARY_CLOUD_NAME"),
    CLOUDINARY_API_KEY=require_env("CLOUDINARY_API_KEY"),
    CLOUDINARY_API_SECRET=require_env("CLOUDINARY_API_SECRET"),
    MONGO_DB_NAME=os.getenv("MONGO_DB_NAME", "fastcars_db"),
    ACCESS_TOKEN_EXPIRE_MINUTES=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080")),
    REGISTRATION_OTP_EXPIRE_MINUTES=int(os.getenv("REGISTRATION_OTP_EXPIRE_MINUTES", "10")),
    REGISTRATION_OTP_LENGTH=int(os.getenv("REGISTRATION_OTP_LENGTH", "6")),
    REGISTRATION_OTP_MAX_ATTEMPTS=int(os.getenv("REGISTRATION_OTP_MAX_ATTEMPTS", "5")),
    FRONTEND_URL=os.getenv("FRONTEND_URL", "http://localhost:8501"),
    JWT_ALGORITHM=os.getenv("JWT_ALGORITHM", "HS256"),
    BREVO_API_KEY=optional_env("BREVO_API_KEY"),
    BREVO_SENDER_EMAIL=optional_env("BREVO_SENDER_EMAIL", "EMAIL_USER"),
    BREVO_SENDER_NAME=optional_env("BREVO_SENDER_NAME", default="Fast Cars") or "Fast Cars",
    BREVO_REPLY_TO_EMAIL=optional_env("BREVO_REPLY_TO_EMAIL"),
    BREVO_REPLY_TO_NAME=optional_env("BREVO_REPLY_TO_NAME"),
    ADMIN_NOTIFICATION_EMAIL=optional_env(
        "ADMIN_NOTIFICATION_EMAIL",
        "BREVO_SENDER_EMAIL",
        "EMAIL_USER",
    ),
)
