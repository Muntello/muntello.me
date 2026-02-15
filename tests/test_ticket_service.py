import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.models import Base, User, Ticket, Message, TicketStatus, ContentType
from app.services.ticket_service import (
    get_or_create_user,
    get_active_ticket,
    create_ticket,
    add_message_to_ticket,
    get_last_closed_ticket,
    get_ticket_by_support_message_id,
    get_ticket_by_support_thread_id,
    create_pending_message,
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


@pytest.mark.asyncio
async def test_add_text_message(db_session):
    """Test adding text message to ticket"""
    from aiogram.types import User as TgUser

    tg_user = TgUser(id=123, is_bot=False, first_name="Test")
    user = await get_or_create_user(db_session, tg_user)
    ticket = await create_ticket(db_session, user.id)

    content = {
        "content_type": ContentType.TEXT,
        "text": "Hello support",
        "file_id": None,
    }

    msg = await add_message_to_ticket(
        db_session,
        ticket,
        content=content,
        user_chat_message_id=100,
        support_chat_message_id=200,
        is_from_user=True,
    )

    assert msg.content_type == ContentType.TEXT
    assert msg.text == "Hello support"
    assert msg.user_chat_message_id == 100
    assert msg.support_chat_message_id == 200
    assert msg.file_id is None
    assert ticket.status == TicketStatus.WAITING_SUPPORT


@pytest.mark.asyncio
async def test_add_photo_message(db_session):
    """Test adding photo message to ticket"""
    from aiogram.types import User as TgUser

    tg_user = TgUser(id=123, is_bot=False, first_name="Test")
    user = await get_or_create_user(db_session, tg_user)
    ticket = await create_ticket(db_session, user.id)

    content = {
        "content_type": ContentType.PHOTO,
        "text": "Check this screenshot",
        "file_id": "AgACAgIAAxkBAAI...",
    }

    msg = await add_message_to_ticket(
        db_session,
        ticket,
        content=content,
        user_chat_message_id=100,
        support_chat_message_id=200,
        is_from_user=True,
    )

    assert msg.content_type == ContentType.PHOTO
    assert msg.file_id == "AgACAgIAAxkBAAI..."
    assert msg.text == "Check this screenshot"


@pytest.mark.asyncio
async def test_add_support_reply_updates_status(db_session):
    """Test that support reply changes status to WAITING_USER"""
    from aiogram.types import User as TgUser

    tg_user = TgUser(id=123, is_bot=False, first_name="Test")
    user = await get_or_create_user(db_session, tg_user)
    ticket = await create_ticket(db_session, user.id)

    content = {
        "content_type": ContentType.TEXT,
        "text": "We'll look into it",
        "file_id": None,
    }

    await add_message_to_ticket(
        db_session,
        ticket,
        content=content,
        support_chat_message_id=300,
        user_chat_message_id=301,
        is_from_user=False,
    )

    assert ticket.status == TicketStatus.WAITING_USER


@pytest.mark.asyncio
async def test_get_ticket_by_support_message_id(db_session):
    """Test finding ticket by support chat message ID"""
    from aiogram.types import User as TgUser

    tg_user = TgUser(id=456, is_bot=False, first_name="Test")
    user = await get_or_create_user(db_session, tg_user)
    ticket = await create_ticket(db_session, user.id)

    content = {
        "content_type": ContentType.TEXT,
        "text": "Hello",
        "file_id": None,
    }

    await add_message_to_ticket(
        db_session,
        ticket,
        content=content,
        user_chat_message_id=100,
        support_chat_message_id=500,
        is_from_user=True,
    )

    # Should find ticket by the support chat message ID
    found = await get_ticket_by_support_message_id(db_session, 500)
    assert found is not None
    assert found.id == ticket.id

    # Should not find ticket for unknown message ID
    not_found = await get_ticket_by_support_message_id(db_session, 999)
    assert not_found is None


@pytest.mark.asyncio
async def test_get_ticket_by_support_message_id_multiple_messages(db_session):
    """Test finding ticket when replying to non-first message in thread"""
    from aiogram.types import User as TgUser

    tg_user = TgUser(id=789, is_bot=False, first_name="Test")
    user = await get_or_create_user(db_session, tg_user)
    ticket = await create_ticket(db_session, user.id)
    ticket.support_thread_id = 1000

    # First message
    content1 = {"content_type": ContentType.TEXT, "text": "First", "file_id": None}
    await add_message_to_ticket(
        db_session, ticket, content=content1,
        user_chat_message_id=10, support_chat_message_id=1001,
        is_from_user=True,
    )

    # Second message
    content2 = {"content_type": ContentType.PHOTO, "text": "", "file_id": "photo_id"}
    await add_message_to_ticket(
        db_session, ticket, content=content2,
        user_chat_message_id=11, support_chat_message_id=1002,
        is_from_user=True,
    )

    # Reply to second message should find the same ticket
    found = await get_ticket_by_support_message_id(db_session, 1002)
    assert found is not None
    assert found.id == ticket.id

    # Reply to thread header should also work (via fallback)
    found_header = await get_ticket_by_support_thread_id(db_session, 1000)
    assert found_header is not None
    assert found_header.id == ticket.id


@pytest.mark.asyncio
async def test_create_pending_message_with_media(db_session):
    """Test creating pending message with media content"""
    from aiogram.types import User as TgUser

    tg_user = TgUser(id=123, is_bot=False, first_name="Test")
    await get_or_create_user(db_session, tg_user)

    content = {
        "content_type": ContentType.VOICE,
        "text": "",
        "file_id": "AwACAgIAAxkBAAI...",
    }

    pending = await create_pending_message(
        db_session,
        user_id=123,
        content=content,
        telegram_message_id=42,
    )

    assert pending.content_type == ContentType.VOICE
    assert pending.file_id == "AwACAgIAAxkBAAI..."
    assert pending.text == ""
