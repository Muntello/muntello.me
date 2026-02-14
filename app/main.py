from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import init_db
from app.api.health import router as health_router
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
    await init_db()
    logger.info("Database initialized")

    yield

    # Shutdown
    logger.info("Shutting down application")


app = FastAPI(
    title="Muntello Support Bot",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(health_router, tags=["health"])
