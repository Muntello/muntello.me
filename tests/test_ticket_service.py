import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.models import Base, User, Ticket, Message, TicketStatus
from app.services.ticket_service import (
    get_or_create_user,
    get_active_ticket,
    create_ticket,
    add_message_to_ticket,
    get_last_closed_ticket
)


@pytest_asyncio.fixture
async def db_session():
    """Create test database session"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_get_or_create_user_creates_new_user(db_session):
    """Test creating new user"""
    from aiogram.types import User as TgUser

    tg_user = TgUser(
        id=123456789,
        is_bot=False,
        first_name="Test",
        last_name="User",
        username="testuser"
    )

    user = await get_or_create_user(db_session, tg_user)

    assert user.id == 123456789
    assert user.first_name == "Test"
    assert user.username == "testuser"


@pytest.mark.asyncio
async def test_create_ticket(db_session):
    """Test ticket creation"""
    from aiogram.types import User as TgUser

    tg_user = TgUser(id=123, is_bot=False, first_name="Test")
    user = await get_or_create_user(db_session, tg_user)

    ticket = await create_ticket(db_session, user.id)

    assert ticket.user_id == user.id
    assert ticket.status == TicketStatus.WAITING_SUPPORT
    assert ticket.id is not None
