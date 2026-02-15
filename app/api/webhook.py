from fastapi import APIRouter, Request, Depends
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
import logging


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/telegram")
async def telegram_webhook(
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    """Telegram webhook endpoint"""
    bot: Bot = request.app.state.bot
    dp: Dispatcher = request.app.state.dp

    # Parse update
    data = await request.json()
    update = Update(**data)

    logger.info("webhook_received", extra={"update_id": update.update_id})

    # Inject session into context for handlers
    await dp.feed_update(bot, update, session=session)

    return {"ok": True}
