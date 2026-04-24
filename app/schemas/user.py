from pydantic import BaseModel, Field, field_validator, ConfigDict


class UserCreate(BaseModel):
    name: str
    email: str
    phone: str
    password: str

    @field_validator("password")
    @classmethod
    def validate_password_length(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        password_bytes = value.encode("utf-8")
        if len(password_bytes) > 72:
            raise ValueError("Password must not be longer than 72 bytes")
        return value

    @field_validator("name", "phone")
    @classmethod
    def strip_text_fields(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Field must not be empty")
        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("Enter a valid email address")
        return value


class UserLogin(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("Enter a valid email address")
        return value


class ForgotPasswordRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("Enter a valid email address")
        return value


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password_length(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        password_bytes = value.encode("utf-8")
        if len(password_bytes) > 72:
            raise ValueError("Password must not be longer than 72 bytes")
        return value


class RegistrationStartResponse(BaseModel):
    message: str
    email: str
    expires_in_minutes: int


class VerifyRegistrationOtpRequest(BaseModel):
    email: str
    otp: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("Enter a valid email address")
        return value

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, value: str) -> str:
        value = value.strip()
        if not value.isdigit():
            raise ValueError("OTP must contain only numbers")
        if len(value) < 4 or len(value) > 8:
            raise ValueError("OTP must be between 4 and 8 digits")
        return value


class ResendRegistrationOtpRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("Enter a valid email address")
        return value


class MessageResponse(BaseModel):
    message: str


class UserUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None

    @field_validator("name", "phone")
    @classmethod
    def strip_optional_text_fields(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Field must not be empty")
        return value


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("current_password")
    @classmethod
    def validate_current_password(cls, value: str) -> str:
        if not value:
            raise ValueError("Current password is required")
        return value

    @field_validator("new_password")
    @classmethod
    def validate_new_password_length(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        password_bytes = value.encode("utf-8")
        if len(password_bytes) > 72:
            raise ValueError("Password must not be longer than 72 bytes")
        return value


class UserOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")
    name: str
    email: str
    phone: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
