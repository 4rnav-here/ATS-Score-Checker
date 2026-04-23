"""
Email Service — sends OTP codes via SMTP.

Uses aiosmtplib for async delivery. Plain text only (fast > decorative).
Dev: Mailpit (localhost:1025, no auth)
Prod: Any SMTP provider (Gmail, Zoho, self-hosted)
"""

import aiosmtplib
from email.message import EmailMessage

from app.core.config import (
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASSWORD,
    SMTP_FROM,
    SMTP_USE_TLS,
)
from app.core.logger import logger


async def send_otp_email(to_email: str, otp_code: str) -> bool:
    """
    Send a login OTP code to the user's email.

    Returns True if sent successfully, False on failure.
    Email is plain text — no fancy HTML. Fast > decorative.
    """
    message = EmailMessage()
    message["From"] = SMTP_FROM
    message["To"] = to_email
    message["Subject"] = "ATS Analyzer — Your Login Code"

    message.set_content(
        f"Your login verification code is:\n\n"
        f"{otp_code}\n\n"
        f"This code expires in 10 minutes.\n\n"
        f"Do not share this code.\n\n"
        f"— ATS Analyzer"
    )

    try:
        await aiosmtplib.send(
            message,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER or None,
            password=SMTP_PASSWORD or None,
            use_tls=SMTP_USE_TLS,
            start_tls=False if not SMTP_USE_TLS else None,
        )
        logger.info(f"OTP email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send OTP email to {to_email}: {e}")
        return False
