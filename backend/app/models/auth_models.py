"""
Authentication Database Models — PostgreSQL tables for passwordless auth + 2FA.

Tables:
    users           — core user identity (email-based, no password)
    email_otp       — one-time email login codes (stored hashed)
    refresh_tokens  — JWT refresh tokens (stored hashed)
    login_audit     — security audit trail for all login events
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    Text,
    DateTime,
    Boolean,
    BigInteger,
    Integer,
    String,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class User(Base):
    """Core user identity — passwordless, email-only."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(320), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    totp_enabled = Column(Boolean, default=False, nullable=False)
    totp_secret = Column(Text, nullable=True)  # encrypted base32 secret
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class EmailOTP(Base):
    """One-time email login codes — ALWAYS stored hashed, never plaintext."""

    __tablename__ = "email_otp"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    otp_hash = Column(Text, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    attempts = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class RefreshToken(Base):
    """JWT refresh tokens — stored hashed in PostgreSQL. Never raw."""

    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(Text, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class LoginAudit(Base):
    """Security audit trail — logs every login attempt (success or failure)."""

    __tablename__ = "login_audit"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    ip_address = Column(Text, nullable=True)
    device_info = Column(Text, nullable=True)
    login_type = Column(String(50), nullable=False)  # "otp" | "totp" | "refresh"
    success = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
