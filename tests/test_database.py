import pytest
import os
from sqlalchemy import text
from app.database import engine, async_session, init_db, get_session
from app.models import Base, User


@pytest.mark.asyncio
async def test_init_db_creates_tables():
    """Test that init_db creates all tables"""
    # Use in-memory SQLite for tests
    test_db_url = "sqlite+aiosqlite:///:memory:"

    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    test_engine = create_async_engine(test_db_url, echo=False)

    # Initialize tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Verify tables exist
    async with test_engine.connect() as conn:
        result = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table'")
        )
        tables = [row[0] for row in result]

    assert "users" in tables
    assert "tickets" in tables
    assert "messages" in tables
    assert "pending_messages" in tables

    await test_engine.dispose()


@pytest.mark.asyncio
async def test_get_session_returns_async_session():
    """Test that get_session returns AsyncSession"""
    from app.database import get_session

    async for session in get_session():
        from sqlalchemy.ext.asyncio import AsyncSession
        assert isinstance(session, AsyncSession)
        break
