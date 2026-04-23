"""
Auth Service — orchestrates the full passwordless login + 2FA flow.

This is the central coordinator. It calls otp_service, totp_service,
jwt_service, email_service, and rate_limit_service. Handlers never
call those services directly — always through auth_service.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.models.auth_models import User, LoginAudit
from app.services import (
    otp_service,
    email_service,
    jwt_service,
    totp_service,
    rate_limit_service,
)


# ── Login Step 1: Request OTP ─────────────────────────────────────────────────

async def request_login_otp(
    db: AsyncSession,
    email: str,
    ip_address: str = "",
    device_info: str = "",
) -> dict:
    """
    Start the passwordless login flow.

    1. Rate limit check
    2. Find or create user
    3. Generate OTP
    4. Email OTP
    5. Log attempt
    """
    # Rate limit check
    allowed = await rate_limit_service.check_otp_rate_limit(email)
    if not allowed:
        return {"success": False, "detail": "Too many requests. Try again later."}

    # Find or create user
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        user = User(email=email)
        db.add(user)
        await db.flush()
        logger.info(f"New user created: {email}")

    # Generate and store OTP
    otp_plain = await otp_service.create_otp(db, str(user.id))

    # Send email
    sent = await email_service.send_otp_email(email, otp_plain)

    if not sent:
        return {"success": False, "detail": "Failed to send OTP email. Try again."}

    # Audit log
    audit = LoginAudit(
        user_id=user.id,
        ip_address=ip_address,
        device_info=device_info,
        login_type="otp_request",
        success=True,
    )
    db.add(audit)
    await db.commit()

    return {"success": True, "detail": "OTP sent to your email."}


# ── Login Step 2: Verify OTP ──────────────────────────────────────────────────

async def verify_login_otp(
    db: AsyncSession,
    email: str,
    otp_input: str,
    ip_address: str = "",
    device_info: str = "",
) -> dict:
    """
    Verify the email OTP.

    If TOTP is NOT enabled → issue JWT tokens immediately.
    If TOTP IS enabled → return requires_2fa=True (frontend redirects to /verify-2fa).
    """
    # Rate limit check
    allowed = await rate_limit_service.check_verify_rate_limit(email)
    if not allowed:
        return {"success": False, "detail": "Too many attempts. Try again later."}

    # Find user
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        return {"success": False, "detail": "Invalid email or OTP."}

    # Validate OTP
    valid = await otp_service.validate_otp(db, str(user.id), otp_input)

    if not valid:
        # Audit failure
        audit = LoginAudit(
            user_id=user.id,
            ip_address=ip_address,
            device_info=device_info,
            login_type="otp_verify",
            success=False,
        )
        db.add(audit)
        await db.commit()
        return {"success": False, "detail": "Invalid or expired OTP."}

    # Mark user as verified
    user.is_verified = True

    # Check if TOTP is required
    if user.totp_enabled:
        # Audit partial success
        audit = LoginAudit(
            user_id=user.id,
            ip_address=ip_address,
            device_info=device_info,
            login_type="otp_verify_needs_totp",
            success=True,
        )
        db.add(audit)
        await db.commit()

        return {
            "success": True,
            "requires_2fa": True,
            "detail": "OTP verified. Enter your authenticator code.",
        }

    # No TOTP — issue tokens
    return await _issue_tokens(db, user, ip_address, device_info)


# ── Login Step 3: Verify TOTP ─────────────────────────────────────────────────

async def verify_totp_login(
    db: AsyncSession,
    email: str,
    totp_code: str,
    ip_address: str = "",
    device_info: str = "",
) -> dict:
    """Verify the TOTP code and issue JWT tokens."""
    # Rate limit check
    allowed = await rate_limit_service.check_verify_rate_limit(email)
    if not allowed:
        return {"success": False, "detail": "Too many attempts. Try again later."}

    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.totp_enabled or not user.totp_secret:
        return {"success": False, "detail": "TOTP not configured."}

    if not totp_service.verify_totp(user.totp_secret, totp_code):
        audit = LoginAudit(
            user_id=user.id,
            ip_address=ip_address,
            device_info=device_info,
            login_type="totp_verify",
            success=False,
        )
        db.add(audit)
        await db.commit()
        return {"success": False, "detail": "Invalid authenticator code."}

    return await _issue_tokens(db, user, ip_address, device_info)


# ── Logout ────────────────────────────────────────────────────────────────────

async def logout(db: AsyncSession, user_id: str, refresh_token: Optional[str] = None) -> dict:
    """Revoke all refresh tokens for the user."""
    await jwt_service.revoke_all_user_tokens(db, user_id)
    await db.commit()
    logger.info(f"User logged out: {user_id}")
    return {"success": True, "detail": "Logged out successfully."}


# ── Refresh Token ─────────────────────────────────────────────────────────────

async def refresh_access_token(db: AsyncSession, refresh_token: str) -> dict:
    """Validate refresh token and issue a new access token."""
    record = await jwt_service.verify_refresh_token(db, refresh_token)

    if not record:
        return {"success": False, "detail": "Invalid or expired refresh token."}

    # Get user
    stmt = select(User).where(User.id == record.user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        return {"success": False, "detail": "User not found."}

    access_token = jwt_service.create_access_token(str(user.id), user.email)

    return {
        "success": True,
        "access_token": access_token,
        "token_type": "bearer",
    }


# ── TOTP Setup ────────────────────────────────────────────────────────────────

async def setup_totp(db: AsyncSession, user: User) -> dict:
    """Generate TOTP secret and QR code for the user."""
    secret = totp_service.generate_totp_secret()
    uri = totp_service.get_totp_uri(secret, user.email)
    qr_base64 = totp_service.generate_qr_code_base64(uri)

    # Store secret (not yet enabled — user must verify first)
    user.totp_secret = secret
    await db.flush()

    return {
        "secret": secret,
        "qr_code_base64": qr_base64,
    }


async def enable_totp(db: AsyncSession, user: User, code: str) -> dict:
    """Verify the TOTP code and enable 2FA for the user."""
    if not user.totp_secret:
        return {"success": False, "detail": "Run TOTP setup first."}

    if not totp_service.verify_totp(user.totp_secret, code):
        return {"success": False, "detail": "Invalid code. Try again."}

    user.totp_enabled = True
    await db.commit()
    logger.info(f"TOTP enabled for user {user.email}")

    return {"success": True, "detail": "Two-factor authentication enabled."}


async def disable_totp(db: AsyncSession, user: User) -> dict:
    """Disable 2FA for the user."""
    user.totp_enabled = False
    user.totp_secret = None
    await db.commit()
    logger.info(f"TOTP disabled for user {user.email}")

    return {"success": True, "detail": "Two-factor authentication disabled."}


# ── Private helpers ───────────────────────────────────────────────────────────

async def _issue_tokens(
    db: AsyncSession,
    user: User,
    ip_address: str,
    device_info: str,
) -> dict:
    """Issue access + refresh tokens and log the event."""
    access_token = jwt_service.create_access_token(str(user.id), user.email)
    refresh_token = jwt_service.create_refresh_token_value()
    await jwt_service.store_refresh_token(db, str(user.id), refresh_token)

    # Audit success
    audit = LoginAudit(
        user_id=user.id,
        ip_address=ip_address,
        device_info=device_info,
        login_type="login_success",
        success=True,
    )
    db.add(audit)
    await db.commit()

    return {
        "success": True,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "totp_enabled": user.totp_enabled,
        },
    }
