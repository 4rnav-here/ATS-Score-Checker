"""
JWT Service — access + refresh token creation, verification, and revocation.

Access Token:  15 min expiry, stateless
Refresh Token: 30 day expiry, stored hashed in PostgreSQL

Never store raw refresh tokens — always hash before persisting.
"""

import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Optional

from jose import jwt, JWTError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from app.core.database import get_db
from app.core.logger import logger
from app.models.auth_models import RefreshToken, User

security = HTTPBearer(auto_error=False)


def _hash_token(token: str) -> str:
    """SHA-256 hash a token for storage (fast, deterministic — good for lookup)."""
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(user_id: str, email: str) -> str:
    """Create a short-lived access token (15 min default)."""
    payload = {
        "sub": user_id,
        "email": email,
        "type": "access",
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token_value() -> str:
    """Generate a random refresh token string."""
    return str(uuid.uuid4()) + "-" + str(uuid.uuid4())


async def store_refresh_token(
    db: AsyncSession, user_id: str, token: str
) -> None:
    """Hash and store a refresh token in PostgreSQL."""
    record = RefreshToken(
        user_id=user_id,
        token_hash=_hash_token(token),
        expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(record)
    await db.flush()
    logger.info(f"Refresh token stored for user_id={user_id}")


def decode_token(token: str) -> dict:
    """Decode and validate a JWT. Raises HTTPException on failure."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )


async def verify_refresh_token(db: AsyncSession, token: str) -> Optional[RefreshToken]:
    """Verify a refresh token exists, is not revoked, and is not expired."""
    token_hash = _hash_token(token)
    stmt = select(RefreshToken).where(
        RefreshToken.token_hash == token_hash,
        RefreshToken.revoked == False,
        RefreshToken.expires_at > datetime.utcnow(),
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def revoke_refresh_token(db: AsyncSession, token: str) -> None:
    """Revoke a specific refresh token."""
    token_hash = _hash_token(token)
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.token_hash == token_hash)
        .values(revoked=True)
    )
    await db.flush()


async def revoke_all_user_tokens(db: AsyncSession, user_id: str) -> None:
    """Revoke ALL refresh tokens for a user (used on logout)."""
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked == False)
        .values(revoked=True)
    )
    await db.flush()
    logger.info(f"All refresh tokens revoked for user_id={user_id}")


# ── FastAPI Dependency — get_current_user ─────────────────────────────────────

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency: extract and validate JWT from Authorization header or cookie.
    Returns the authenticated User object.
    """
    token = None

    # Try Authorization header first
    if credentials:
        token = credentials.credentials

    # Fall back to cookie
    if not token:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
        )

    payload = decode_token(token)

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type.",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload.",
        )

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    return user
