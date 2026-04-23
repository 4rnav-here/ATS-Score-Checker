"""
Alerts API — manages Telegram user alert subscriptions.
Called by the Telegram bot to enable/disable daily job alerts.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logger import logger
from app.models.analysis import UserAlert

router = APIRouter()


class AlertRequest(BaseModel):
    chat_id: int
    analysis_id: str
    enabled: bool


class AlertResponse(BaseModel):
    chat_id: int
    enabled: bool
    message: str


@router.post("/alerts", response_model=AlertResponse, summary="Manage job alert subscriptions")
async def manage_alert(
    request: AlertRequest,
    db: AsyncSession = Depends(get_db),
) -> AlertResponse:
    """
    Enable or disable daily job alerts for a Telegram user.

    Uses UPSERT logic — a user can only have one active alert.
    """
    # Check if user already has an alert
    stmt = select(UserAlert).where(UserAlert.chat_id == request.chat_id)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if request.enabled:
        if existing:
            # Update existing alert
            existing.analysis_id = request.analysis_id
            existing.alert_enabled = True
            message = "Alert updated with new analysis."
        else:
            # Create new alert
            alert = UserAlert(
                chat_id=request.chat_id,
                analysis_id=request.analysis_id,
                alert_enabled=True,
            )
            db.add(alert)
            message = "Daily job alert enabled."
    else:
        if existing:
            existing.alert_enabled = False
            message = "Daily job alert disabled."
        else:
            message = "No active alert found."

    await db.commit()
    logger.info(f"Alert {'enabled' if request.enabled else 'disabled'} for chat_id={request.chat_id}")

    return AlertResponse(
        chat_id=request.chat_id,
        enabled=request.enabled,
        message=message,
    )
