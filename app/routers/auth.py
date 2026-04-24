from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.dependencies import get_current_user
from app.schemas.user import (
    ForgotPasswordRequest,
    MessageResponse,
    RegistrationStartResponse,
    ResendRegistrationOtpRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserOut,
    VerifyRegistrationOtpRequest,
)
from app.auth.utils import (
    create_access_token,
    decode_token,
    generate_otp,
    hash_password,
    verify_password,
)
from app.core.config import settings
from app.core.email import (
    build_password_reset_email,
    build_registration_otp_email,
    queue_email,
)
from app.db import get_db, parse_object_id, utcnow

router = APIRouter(prefix="/api/auth", tags=["auth"])


def build_user_response(user: dict) -> UserOut:
    return UserOut(
        _id=str(user["_id"]),
        name=user["name"],
        email=user["email"],
        phone=user["phone"],
        role=user["role"],
    )


def build_registration_response(email: str) -> RegistrationStartResponse:
    return RegistrationStartResponse(
        message="Verification code sent to your email",
        email=email,
        expires_in_minutes=settings.REGISTRATION_OTP_EXPIRE_MINUTES,
    )


def ensure_utc_datetime(value: datetime | None) -> datetime:
    if value is None:
        return utcnow()
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


async def save_pending_registration(payload: UserCreate, db) -> str:
    otp = generate_otp()
    now = utcnow()
    expires_at = now + timedelta(minutes=settings.REGISTRATION_OTP_EXPIRE_MINUTES)
    document = {
        "name": payload.name,
        "email": payload.email,
        "phone": payload.phone,
        "password_hash": hash_password(payload.password),
        "otp_hash": hash_password(otp),
        "attempt_count": 0,
        "created_at": now,
        "otp_sent_at": now,
        "expires_at": expires_at,
    }

    await db.pending_registrations.delete_one({"email": payload.email})
    await db.pending_registrations.insert_one(document)
    return otp


async def refresh_registration_otp(email: str, db) -> tuple[dict, str]:
    pending = await db.pending_registrations.find_one({"email": email})
    if not pending:
        raise HTTPException(status_code=404, detail="No pending registration found for this email")

    otp = generate_otp()
    now = utcnow()
    await db.pending_registrations.update_one(
        {"_id": pending["_id"]},
        {
            "$set": {
                "otp_hash": hash_password(otp),
                "attempt_count": 0,
                "otp_sent_at": now,
                "expires_at": now + timedelta(minutes=settings.REGISTRATION_OTP_EXPIRE_MINUTES),
            }
        },
    )
    pending = await db.pending_registrations.find_one({"_id": pending["_id"]})
    return pending, otp


async def authenticate_user(email: str, password: str, db):
    normalized_email = email.lower()
    user = await db.users.find_one({"email": normalized_email})
    if user:
        if not user.get("is_verified", True):
            raise HTTPException(status_code=403, detail="Please verify your email before logging in")
        if not verify_password(password, user["password_hash"]):
            return None
        return user

    pending = await db.pending_registrations.find_one({"email": normalized_email})
    if pending:
        raise HTTPException(status_code=403, detail="Please verify your email before logging in")
    return None


@router.post(
    "/register",
    response_model=RegistrationStartResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: UserCreate,
    background_tasks: BackgroundTasks,
    db=Depends(get_db),
):
    existing = await db.users.find_one({"email": payload.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    otp = await save_pending_registration(payload, db)
    email_content = build_registration_otp_email(
        name=payload.name,
        otp=otp,
        expires_in_minutes=settings.REGISTRATION_OTP_EXPIRE_MINUTES,
    )
    queue_email(
        background_tasks,
        subject="Verify your Fast Cars account",
        to_email=payload.email,
        body=email_content.text,
        html_body=email_content.html,
    )
    return build_registration_response(payload.email)


@router.post("/register/verify-otp", response_model=TokenResponse)
async def verify_registration_otp(payload: VerifyRegistrationOtpRequest, db=Depends(get_db)):
    existing = await db.users.find_one({"email": payload.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already verified. Please log in.")

    pending = await db.pending_registrations.find_one({"email": payload.email})
    if not pending:
        raise HTTPException(status_code=404, detail="No pending registration found for this email")

    expires_at = ensure_utc_datetime(pending.get("expires_at"))
    if expires_at <= utcnow():
        await db.pending_registrations.delete_one({"_id": pending["_id"]})
        raise HTTPException(status_code=400, detail="OTP has expired. Request a new code.")

    next_attempt_count = pending.get("attempt_count", 0) + 1
    if not verify_password(payload.otp, pending["otp_hash"]):
        if next_attempt_count >= settings.REGISTRATION_OTP_MAX_ATTEMPTS:
            await db.pending_registrations.delete_one({"_id": pending["_id"]})
            raise HTTPException(status_code=400, detail="Too many invalid attempts. Request a new code.")
        await db.pending_registrations.update_one(
            {"_id": pending["_id"]},
            {"$set": {"attempt_count": next_attempt_count}},
        )
        raise HTTPException(status_code=400, detail="Invalid OTP")

    user = {
        "name": pending["name"],
        "email": pending["email"],
        "phone": pending["phone"],
        "password_hash": pending["password_hash"],
        "role": "user",
        "is_verified": True,
        "created_at": ensure_utc_datetime(pending.get("created_at")),
        "email_verified_at": utcnow(),
    }
    result = await db.users.insert_one(user)
    await db.pending_registrations.delete_one({"_id": pending["_id"]})

    token = create_access_token({"sub": str(result.inserted_id)})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/register/resend-otp", response_model=RegistrationStartResponse)
async def resend_registration_otp(
    payload: ResendRegistrationOtpRequest,
    background_tasks: BackgroundTasks,
    db=Depends(get_db),
):
    existing = await db.users.find_one({"email": payload.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    pending, otp = await refresh_registration_otp(payload.email, db)
    email_content = build_registration_otp_email(
        name=pending["name"],
        otp=otp,
        expires_in_minutes=settings.REGISTRATION_OTP_EXPIRE_MINUTES,
    )
    queue_email(
        background_tasks,
        subject="Your new Fast Cars verification code",
        to_email=pending["email"],
        body=email_content.text,
        html_body=email_content.html,
    )
    return build_registration_response(payload.email)


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
) -> MessageResponse:
    user = await db.users.find_one({"email": payload.email})
    if user:
        reset_token = create_access_token({"sub": str(user["_id"]), "scope": "password_reset"})
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        email_content = build_password_reset_email(name=user["name"], reset_url=reset_url)
        queue_email(
            background_tasks,
            subject="Fast Cars password reset",
            to_email=user["email"],
            body=email_content.text,
            html_body=email_content.html,
        )
    return MessageResponse(message="If that email is registered, a reset link has been sent")


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
