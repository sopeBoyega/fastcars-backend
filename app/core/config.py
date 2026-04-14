import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


@dataclass(frozen=True)
class Settings:
    MONGO_URI: str
    SECRET_KEY: str
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str
    EMAIL_USER: str
    EMAIL_PASSWORD: str
    MONGO_DB_NAME: str = "fastcars_db"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080
    FRONTEND_URL: str = "http://localhost:8501"
    JWT_ALGORITHM: str = "HS256"


settings = Settings(
    MONGO_URI=require_env("MONGO_URI"),
    SECRET_KEY=require_env("SECRET_KEY"),
    CLOUDINARY_CLOUD_NAME=require_env("CLOUDINARY_CLOUD_NAME"),
    CLOUDINARY_API_KEY=require_env("CLOUDINARY_API_KEY"),
    CLOUDINARY_API_SECRET=require_env("CLOUDINARY_API_SECRET"),
    EMAIL_USER=require_env("EMAIL_USER"),
    EMAIL_PASSWORD=require_env("EMAIL_PASSWORD"),
    MONGO_DB_NAME=os.getenv("MONGO_DB_NAME", "fastcars_db"),
    ACCESS_TOKEN_EXPIRE_MINUTES=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080")),
    FRONTEND_URL=os.getenv("FRONTEND_URL", "http://localhost:8501"),
    JWT_ALGORITHM=os.getenv("JWT_ALGORITHM", "HS256"),
)
