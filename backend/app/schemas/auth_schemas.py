from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
from app.models.user_models import Role


# ─── Registration ──────────────────────────────────────────
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    password: str
    role: Role = Role.USER

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("username")
    @classmethod
    def username_clean(cls, v: str) -> str:
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        return v.lower().strip()


# ─── Login ─────────────────────────────────────────────────
class UserLogin(BaseModel):
    username: str
    password: str


# ─── MFA ───────────────────────────────────────────────────
class MFASetupResponse(BaseModel):
    secret: str
    qr_uri: str
    backup_codes: list[str]


class MFAVerify(BaseModel):
    temp_token: str
    totp_code: str


class MFAEnableRequest(BaseModel):
    totp_code: str


# ─── Responses ─────────────────────────────────────────────
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    requires_mfa: bool = False
    temp_token: Optional[str] = None
    user_id: str
    username: str
    role: str


class UserOut(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str]
    role: Role
    is_active: bool
    mfa_enabled: bool
    failed_login_attempts: int
    last_login: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    role: Optional[Role] = None
