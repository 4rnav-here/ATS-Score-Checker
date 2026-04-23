"""
TOTP Service — authenticator app (Google Auth, Authy, etc.) second factor.

Uses pyotp for TOTP generation/verification and qrcode for QR image generation.
"""

import base64
import io

import pyotp
import qrcode

from app.core.logger import logger


def generate_totp_secret() -> str:
    """Generate a new random TOTP secret (base32 encoded)."""
    return pyotp.random_base32()


def get_totp_uri(secret: str, email: str) -> str:
    """Get the provisioning URI for QR code generation."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(
        name=email,
        issuer_name="ATS Analyzer",
    )


def generate_qr_code_base64(uri: str) -> str:
    """
    Generate a QR code image and return as base64-encoded PNG string.

    Frontend renders this directly: <img src="data:image/png;base64,{qr_code_base64}" />
    """
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def verify_totp(secret: str, code: str) -> bool:
    """
    Verify a TOTP code from the user's authenticator app.

    Uses a 1-step window (valid_window=1) to handle slight time drift.
    """
    totp = pyotp.TOTP(secret)
    is_valid = totp.verify(code, valid_window=1)

    if is_valid:
        logger.info("TOTP verification succeeded")
    else:
        logger.warning("TOTP verification failed")

    return is_valid
