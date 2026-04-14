from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from app.auth.dependencies import get_current_user
from app.schemas.user import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserOut,
)
from app.auth.utils import create_access_token, decode_token, hash_password, verify_password
from app.core.config import settings
from app.core.email import queue_email
from app.db import get_db, parse_object_id

router = APIRouter(prefix="/api/auth", tags=["auth"])


def build_user_response(user: dict) -> UserOut:
    return UserOut(
        _id=str(user["_id"]),
        name=user["name"],
        email=user["email"],
        phone=user["phone"],
        role=user["role"],
    )


async def authenticate_user(email: str, password: str, db):
    user = await db.users.find_one({"email": email.lower()})
    if not user or not verify_password(password, user["password_hash"]):
        return None
    return user


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(payload: UserCreate, db=Depends(get_db)):
    existing = await db.users.find_one({"email": payload.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = payload.model_dump()
    password = user.pop("password")
    user["password_hash"] = hash_password(password)
    user["role"] = "user"

    result = await db.users.insert_one(user)
    token = create_access_token({"sub": str(result.inserted_id)})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin, db=Depends(get_db)):
    user = await authenticate_user(
        email=payload.email,
        password=payload.password,
        db=db,
    )
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(user["_id"])})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/token", response_model=TokenResponse)
async def issue_token(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    user = await authenticate_user(
        email=form_data.username,
        password=form_data.password,
        db=db,
    )
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(user["_id"])})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/forgot-password")
async def forgot_password(
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db=Depends(get_db),
):
    user = await db.users.find_one({"email": payload.email})
    if user:
        reset_token = create_access_token({"sub": str(user["_id"]), "scope": "password_reset"})
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        queue_email(
            background_tasks,
            subject="Fast Cars password reset",
            to_email=user["email"],
            body=f"Use this link to reset your password: {reset_url}",
        )
    return {"message": "If that email is registered, a reset link has been sent"}


@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest, db=Depends(get_db)):
    try:
        token_payload = decode_token(payload.token)
        if token_payload.get("scope") != "password_reset":
            raise HTTPException(status_code=400, detail="Invalid reset token")
        user_id = parse_object_id(token_payload.get("sub"), "user_id")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user = await db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.users.update_one(
        {"_id": user_id},
        {"$set": {"password_hash": hash_password(payload.new_password)}},
    )
    return {"message": "Password reset successful"}


@router.get("/me", response_model=UserOut)
async def get_me(current_user=Depends(get_current_user)):
    return build_user_response(current_user)
