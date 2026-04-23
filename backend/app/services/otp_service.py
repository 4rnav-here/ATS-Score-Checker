"""
OTP Service — cryptographically secure 6-digit code generation + validation.

Rules (non-negotiable):
    - 6 digits, cryptographically secure (secrets, NOT random.randint)
    - 10 min expiry
    - Max 5 verification attempts
    - Single active OTP only (new OTP invalidates old)
    - OTP invalid after use
    - ALWAYS stored hashed (bcrypt), NEVER plaintext
"""

import secrets
from datetime import datetime, timedelta

import bcrypt as _bcrypt
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import OTP_EXPIRE_MINUTES, OTP_MAX_ATTEMPTS
from app.core.logger import logger
from app.models.auth_models import EmailOTP


def generate_otp() -> str:
    """Generate a cryptographically secure 6-digit OTP."""
    return str(secrets.randbelow(900000) + 100000)


def hash_otp(otp: str) -> str:
    """Hash an OTP using bcrypt."""
    return _bcrypt.hashpw(otp.encode(), _bcrypt.gensalt()).decode()


def verify_otp_hash(otp: str, otp_hash: str) -> bool:
    """Verify an OTP against its bcrypt hash."""
    return _bcrypt.checkpw(otp.encode(), otp_hash.encode())


async def create_otp(db: AsyncSession, user_id: str) -> str:
    """
    Create a new OTP for a user.

    1. Invalidates all previous unused OTPs for this user
    2. Generates a new cryptographically secure OTP
    3. Stores the HASHED OTP in the database
    4. Returns the PLAINTEXT OTP (for email delivery only)
    """
    # Invalidate all previous OTPs for this user
    await db.execute(
        update(EmailOTP)
        .where(EmailOTP.user_id == user_id, EmailOTP.is_used == False)
        .values(is_used=True)
    )

    # Generate new OTP
    otp_plain = generate_otp()
    otp_hashed = hash_otp(otp_plain)

    otp_record = EmailOTP(
        user_id=user_id,
        otp_hash=otp_hashed,
        expires_at=datetime.utcnow() + timedelta(minutes=OTP_EXPIRE_MINUTES),
    )
    db.add(otp_record)
    await db.flush()

    logger.info(f"OTP created for user_id={user_id}")
    return otp_plain


async def validate_otp(db: AsyncSession, user_id: str, otp_input: str) -> bool:
    """
    Validate an OTP input against the stored hash.

    Checks: not expired, not used, attempts < max, hash matches.
    Marks OTP as used on success. Increments attempts on failure.
    """
    # Fetch the latest unused OTP for this user
    stmt = (
        select(EmailOTP)
        .where(
            EmailOTP.user_id == user_id,
            EmailOTP.is_used == False,
            EmailOTP.expires_at > datetime.utcnow(),
        )
        .order_by(EmailOTP.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    otp_record = result.scalar_one_or_none()

    if not otp_record:
        logger.warning(f"OTP validation failed: no valid OTP for user_id={user_id}")
        return False

    # Check attempt limit
    if otp_record.attempts >= OTP_MAX_ATTEMPTS:
        otp_record.is_used = True  # Lock it out
        await db.flush()
        logger.warning(f"OTP locked: max attempts reached for user_id={user_id}")
        return False

    # Verify the hash
    if not verify_otp_hash(otp_input, otp_record.otp_hash):
        otp_record.attempts += 1
        await db.flush()
        logger.warning(f"OTP mismatch: attempt {otp_record.attempts} for user_id={user_id}")
        return False

    # Success — mark as used
    otp_record.is_used = True
    await db.flush()
    logger.info(f"OTP validated successfully for user_id={user_id}")
    return True
