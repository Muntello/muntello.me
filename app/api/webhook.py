from fastapi import APIRouter, Request, Depends, HTTPException, status
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.config import settings
import logging


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/telegram")
async def telegram_webhook(
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    """Telegram webhook endpoint"""
    # Verify webhook secret
    secret_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if secret_header != settings.TELEGRAM_WEBHOOK_SECRET:
        logger.warning("Invalid webhook secret", extra={
            "ip": request.client.host if request.client else "unknown"
        })
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid secret token"
        )

    bot: Bot = request.app.state.bot
    dp: Dispatcher = request.app.state.dp

    # Parse update
    data = await request.json()
    update = Update(**data)

    logger.info("webhook_received", extra={"update_id": update.update_id})

    # Inject session into context for handlers
    await dp.feed_update(bot, update, session=session)

    return {"ok": True}
