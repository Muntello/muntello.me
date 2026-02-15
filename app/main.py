from fastapi import FastAPI
from contextlib import asynccontextmanager
from aiogram import Bot, Dispatcher
from app.config import settings
from app.database import init_db
from app.api.health import router as health_router
from app.api.webhook import router as webhook_router
from app.bot.handlers import setup_handlers
from app.utils.logger import setup_logging
import logging


# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    logger.info("Starting application")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Create bot and dispatcher
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()

    # Setup handlers
    setup_handlers(dp)
    logger.info("Bot handlers configured")

    # Set webhook
    webhook_url = f"{settings.WEBHOOK_URL}/webhook/telegram"
    await bot.set_webhook(
        url=webhook_url,
        secret_token=settings.TELEGRAM_WEBHOOK_SECRET,
        drop_pending_updates=True
    )
    logger.info("Webhook set", extra={"url": webhook_url})

    # Store in app state
    app.state.bot = bot
    app.state.dp = dp

    yield

    # Shutdown
    logger.info("Shutting down application")
    await bot.delete_webhook()
    await bot.session.close()
    logger.info("Application stopped")


app = FastAPI(
    title="Muntello Support Bot",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(health_router)
app.include_router(webhook_router, prefix="/webhook")

logger.info("Application configured")
