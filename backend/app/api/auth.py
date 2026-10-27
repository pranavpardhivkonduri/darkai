"""
Authentication API Router
"""

import pyotp
import qrcode
import io
import base64
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.user_models import User, MFASession, Role
from app.schemas.auth_schemas import (
    UserRegister, UserLogin, TokenResponse,
    MFAVerify, MFASetupResponse, MFAEnableRequest,
    UserOut, UserUpdate
)
from app.auth.security import (
    get_password_hash, verify_password,
    create_access_token, create_temp_token, verify_token
)
from app.auth.dependencies import get_current_user, require_admin
from app.services.audit_service import create_audit_event
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

MAX_FAILED_ATTEMPTS = 5


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    # Check duplicates
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=409, detail="Username already taken")

    user = User(
        username=payload.username,
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password),
        role=payload.role,
        is_active=True,
        mfa_enabled=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    create_audit_event(
        db, "USER_REGISTERED",
        user_id=user.id,
        result_label=f"User {user.username} registered",
    )

    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        (User.username == payload.username) | (User.email == payload.username)
    ).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                user.is_active = False
            db.commit()
            create_audit_event(
                db, "LOGIN_FAILED",
                user_id=user.id,
                result_label="Invalid credentials",
                details={"attempts": user.failed_login_attempts},
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account locked due to too many failed attempts. Contact admin.",
        )

    # Reset failed attempts on successful auth
    user.failed_login_attempts = 0
    user.last_login = datetime.utcnow()
    db.commit()

    if user.mfa_enabled and user.mfa_secret:
        # Issue short-lived temp token — full token after MFA
        temp = create_temp_token({"sub": user.id, "type": "temp"}, expires_minutes=10)

        # Create MFA session
        mfa_session = MFASession(
            user_id=user.id,
            temp_token=temp,
            expires_at=datetime.utcnow() + timedelta(minutes=10),
        )
        db.add(mfa_session)
        db.commit()

        create_audit_event(
            db, "LOGIN_MFA_REQUIRED",
            user_id=user.id,
            result_label="MFA challenge issued",
        )

        return TokenResponse(
            access_token="",
            requires_mfa=True,
            temp_token=temp,
            user_id=user.id,
            username=user.username,
            role=user.role.value,
        )

    # No MFA — issue full access token
    token = create_access_token({"sub": user.id, "role": user.role.value})
    create_audit_event(
        db, "LOGIN_SUCCESS",
        user_id=user.id,
        result_label="Login successful",
    )

    return TokenResponse(
        access_token=token,
        requires_mfa=False,
        user_id=user.id,
        username=user.username,
        role=user.role.value,
    )


@router.post("/mfa/verify", response_model=TokenResponse)
def verify_mfa(payload: MFAVerify, db: Session = Depends(get_db)):
    token_data = verify_token(payload.temp_token)
    if not token_data or token_data.get("type") != "temp":
        raise HTTPException(status_code=401, detail="Invalid or expired temp token")

    user_id = token_data.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.mfa_secret:
        raise HTTPException(status_code=401, detail="User not found or MFA not configured")

    # Verify TOTP
    totp = pyotp.TOTP(user.mfa_secret)
    if not totp.verify(payload.totp_code, valid_window=1):
        create_audit_event(db, "MFA_FAILED", user_id=user.id, result_label="Invalid TOTP code")
        raise HTTPException(status_code=401, detail="Invalid MFA code")

    # Issue full token
    token = create_access_token({"sub": user.id, "role": user.role.value})
    create_audit_event(db, "MFA_SUCCESS", user_id=user.id, result_label="MFA verified")

    return TokenResponse(
        access_token=token,
        requires_mfa=False,
        user_id=user.id,
        username=user.username,
        role=user.role.value,
    )


@router.get("/mfa/setup", response_model=MFASetupResponse)
def mfa_setup(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Generate a new TOTP secret and QR code for the current user."""
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=current_user.email, issuer_name=settings.MFA_ISSUER)

    # Generate QR code as base64
    qr = qrcode.make(uri)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    # Temporarily store secret in session (user must confirm with enable)
    current_user.mfa_secret = secret
    db.commit()

    return MFASetupResponse(
        secret=secret,
        qr_uri=f"data:image/png;base64,{qr_b64}",
        backup_codes=[pyotp.random_base32()[:8] for _ in range(6)],
    )


@router.post("/mfa/enable")
def enable_mfa(
    payload: MFAEnableRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Verify TOTP code and enable MFA for the current user."""
    if not current_user.mfa_secret:
        raise HTTPException(status_code=400, detail="MFA setup not initiated. Call /auth/mfa/setup first.")

    totp = pyotp.TOTP(current_user.mfa_secret)
    if not totp.verify(payload.totp_code, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid TOTP code. MFA not enabled.")

    current_user.mfa_enabled = True
    db.commit()
    create_audit_event(db, "MFA_ENABLED", user_id=current_user.id, result_label="MFA enabled")

    return {"message": "MFA enabled successfully"}


@router.post("/mfa/disable")
def disable_mfa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user.mfa_enabled = False
    current_user.mfa_secret = None
    db.commit()
    create_audit_event(db, "MFA_DISABLED", user_id=current_user.id, result_label="MFA disabled")
    return {"message": "MFA disabled"}


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


# ─── Admin: User Management ────────────────────────────────
@router.get("/users", response_model=List[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return db.query(User).all()


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: str,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.email is not None:
        user.email = payload.email
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.role is not None:
        user.role = payload.role

    db.commit()
    db.refresh(user)
    return user
