from collections import OrderedDict

from fastapi import APIRouter, Request, Depends, HTTPException, status
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.config import settings
import logging


logger = logging.getLogger(__name__)
router = APIRouter()

_processed_updates: OrderedDict[int, bool] = OrderedDict()
_MAX_CACHE_SIZE = 1000


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

    # Deduplicate: skip already-processed updates (Telegram retries)
    if update.update_id in _processed_updates:
        logger.info("duplicate_update_skipped", extra={"update_id": update.update_id})
        return {"ok": True}

    # Log incoming update details for debugging
    chat_id = None
    if update.message:
        chat_id = update.message.chat.id
        chat_type = update.message.chat.type
        logger.info("webhook_received", extra={
            "update_id": update.update_id,
            "chat_id": chat_id,
            "chat_type": chat_type,
            "from_user": update.message.from_user.id if update.message.from_user else None
        })
    else:
        logger.info("webhook_received", extra={"update_id": update.update_id})

    # Process update — cache only on success so Telegram retries work after failures
    await dp.feed_update(bot, update, session=session)

    _processed_updates[update.update_id] = True
    if len(_processed_updates) > _MAX_CACHE_SIZE:
        _processed_updates.popitem(last=False)

    return {"ok": True}
