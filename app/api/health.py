from fastapi import APIRouter, status, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.database import get_session
import logging


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check(session: AsyncSession = Depends(get_session)):
    """Health check endpoint"""
    try:
        # Check database connection
        result = await session.execute(text("SELECT 1"))
        db_ok = result.scalar() == 1

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "ok" if db_ok else "error",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }, status.HTTP_503_SERVICE_UNAVAILABLE


@router.get("/metrics")
async def metrics(session: AsyncSession = Depends(get_session)):
    """Basic metrics endpoint"""
    try:
        # Count active tickets
        active_result = await session.execute(
            text("SELECT COUNT(*) FROM tickets WHERE status != 'closed'")
        )
        active_tickets = active_result.scalar() or 0

        # Count recent messages
        recent_result = await session.execute(
            text("SELECT COUNT(*) FROM messages WHERE created_at > datetime('now', '-1 hour')")
        )
        messages_last_hour = recent_result.scalar() or 0

        return {
            "active_tickets": active_tickets,
            "messages_last_hour": messages_last_hour,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Metrics fetch failed: {str(e)}")
        return {
            "error": str(e)
        }, status.HTTP_500_INTERNAL_SERVER_ERROR
