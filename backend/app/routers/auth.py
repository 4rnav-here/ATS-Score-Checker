"""
Auth API Router — passwordless login + 2FA endpoints.

Endpoints:
    POST /api/auth/request-login-otp  — send OTP to email
    POST /api/auth/verify-login-otp   — verify OTP, get tokens or require TOTP
    POST /api/auth/verify-totp        — verify 2FA, get tokens
    POST /api/auth/logout             — revoke refresh tokens
    POST /api/auth/refresh            — refresh access token
    GET  /api/auth/me                 — get current user (protected)
    GET  /api/auth/totp/setup         — get QR + secret (protected)
    POST /api/auth/totp/enable        — enable TOTP (protected)
    POST /api/auth/totp/disable       — disable TOTP (protected)
"""

from typing import Optional

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.auth_models import User
from app.services import auth_service
from app.services.jwt_service import get_current_user

router = APIRouter(prefix="/auth")


# ── Request / Response models ─────────────────────────────────────────────────

class RequestOTPInput(BaseModel):
    email: EmailStr


class VerifyOTPInput(BaseModel):
    email: EmailStr
    otp: str


class VerifyTOTPInput(BaseModel):
    email: EmailStr
    code: str


class RefreshInput(BaseModel):
    refresh_token: str


class EnableTOTPInput(BaseModel):
    code: str


class AuthResponse(BaseModel):
    success: bool
    detail: str = ""
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: Optional[str] = None
    requires_2fa: Optional[bool] = None
    user: Optional[dict] = None


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    totp_enabled: bool
    is_verified: bool


class TOTPSetupResponse(BaseModel):
    secret: str
    qr_code_base64: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/request-login-otp", response_model=AuthResponse, summary="Send login OTP to email")
async def request_login_otp(
    body: RequestOTPInput,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """
    Start passwordless login. Creates user if new, sends 6-digit OTP via email.
    """
    ip = request.client.host if request.client else ""
    device = request.headers.get("user-agent", "")

    result = await auth_service.request_login_otp(
        db=db,
        email=body.email,
        ip_address=ip,
        device_info=device,
    )
    return AuthResponse(**result)


@router.post("/verify-login-otp", response_model=AuthResponse, summary="Verify email OTP")
async def verify_login_otp(
    body: VerifyOTPInput,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """
    Verify OTP. If TOTP disabled → returns tokens. If TOTP enabled → requires_2fa=True.
    Sets access_token as httpOnly cookie for frontend middleware.
    """
    ip = request.client.host if request.client else ""
    device = request.headers.get("user-agent", "")

    result = await auth_service.verify_login_otp(
        db=db,
        email=body.email,
        otp_input=body.otp,
        ip_address=ip,
        device_info=device,
    )

    # Set cookie if tokens were issued
    if result.get("access_token"):
        response.set_cookie(
            key="access_token",
            value=result["access_token"],
            httponly=True,
            samesite="lax",
            max_age=900,  # 15 min
            secure=False,  # Set True in production with HTTPS
        )
        response.set_cookie(
            key="refresh_token",
            value=result["refresh_token"],
            httponly=True,
            samesite="lax",
            max_age=30 * 24 * 3600,  # 30 days
            secure=False,
        )

    return AuthResponse(**result)


@router.post("/verify-totp", response_model=AuthResponse, summary="Verify TOTP 2FA code")
async def verify_totp(
    body: VerifyTOTPInput,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """Verify authenticator app code and issue JWT tokens."""
    ip = request.client.host if request.client else ""
    device = request.headers.get("user-agent", "")

    result = await auth_service.verify_totp_login(
        db=db,
        email=body.email,
        totp_code=body.code,
        ip_address=ip,
        device_info=device,
    )

    if result.get("access_token"):
        response.set_cookie(
            key="access_token",
            value=result["access_token"],
            httponly=True,
            samesite="lax",
            max_age=900,
            secure=False,
        )
        response.set_cookie(
            key="refresh_token",
            value=result["refresh_token"],
            httponly=True,
            samesite="lax",
            max_age=30 * 24 * 3600,
            secure=False,
        )

    return AuthResponse(**result)


@router.post("/logout", response_model=AuthResponse, summary="Logout and revoke tokens")
async def logout(
    response: Response,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """Revoke all refresh tokens and clear cookies."""
    result = await auth_service.logout(db=db, user_id=str(user.id))

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return AuthResponse(**result)


@router.post("/refresh", response_model=AuthResponse, summary="Refresh access token")
async def refresh_token(
    body: RefreshInput,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """Validate refresh token and issue a new access token."""
    # Also check cookie if body is empty
    token = body.refresh_token or request.cookies.get("refresh_token", "")

    result = await auth_service.refresh_access_token(db=db, refresh_token=token)

    if result.get("access_token"):
        response.set_cookie(
            key="access_token",
            value=result["access_token"],
            httponly=True,
            samesite="lax",
            max_age=900,
            secure=False,
        )

    return AuthResponse(**result)


@router.get("/me", response_model=UserResponse, summary="Get current authenticated user")
async def get_me(user: User = Depends(get_current_user)) -> UserResponse:
    """Returns the currently authenticated user's profile."""
    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        totp_enabled=user.totp_enabled,
        is_verified=user.is_verified,
    )


@router.get("/totp/setup", response_model=TOTPSetupResponse, summary="Get TOTP setup QR code")
async def totp_setup(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TOTPSetupResponse:
    """Generate TOTP secret + QR code for authenticator app setup."""
    result = await auth_service.setup_totp(db=db, user=user)
    return TOTPSetupResponse(**result)


@router.post("/totp/enable", response_model=AuthResponse, summary="Enable TOTP after verification")
async def totp_enable(
    body: EnableTOTPInput,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """Verify the TOTP code from the authenticator app and enable 2FA."""
    result = await auth_service.enable_totp(db=db, user=user, code=body.code)
    return AuthResponse(**result)


@router.post("/totp/disable", response_model=AuthResponse, summary="Disable TOTP 2FA")
async def totp_disable(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """Disable two-factor authentication."""
    result = await auth_service.disable_totp(db=db, user=user)
    return AuthResponse(**result)
