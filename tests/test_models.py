import pytest
from datetime import datetime
from app.models import User, Ticket, Message, PendingMessage, TicketStatus, ContentType


def test_user_creation():
    """Test User model creation"""
    user = User(
        id=123456789,
        username="testuser",
        first_name="Test",
        last_name="User"
    )
    assert user.id == 123456789
    assert user.username == "testuser"
    assert user.first_name == "Test"
    assert user.is_blocked is False


def test_ticket_status_enum():
    """Test TicketStatus enum values"""
    assert TicketStatus.OPEN == "open"
    assert TicketStatus.WAITING_SUPPORT == "waiting_support"
    assert TicketStatus.WAITING_USER == "waiting_user"
    assert TicketStatus.CLOSED == "closed"


def test_content_type_enum():
    """Test ContentType enum values"""
    assert ContentType.TEXT == "text"
    assert ContentType.PHOTO == "photo"
    assert ContentType.STICKER == "sticker"
    assert ContentType.VOICE == "voice"
    assert ContentType.VIDEO_NOTE == "video_note"
    assert ContentType.ANIMATION == "animation"


def test_ticket_creation():
    """Test Ticket model creation"""
    ticket = Ticket(
        id=1,
        user_id=123456789,
        status=TicketStatus.OPEN
    )
    assert ticket.id == 1
    assert ticket.user_id == 123456789
    assert ticket.status == TicketStatus.OPEN
    assert ticket.closed_by is None


def test_message_with_dual_ids():
    """Test Message model with dual message IDs"""
    msg = Message(
        id=1,
        ticket_id=1,
        user_chat_message_id=100,
        support_chat_message_id=200,
        is_from_user=True,
        content_type=ContentType.TEXT,
        text="Hello",
    )
    assert msg.user_chat_message_id == 100
    assert msg.support_chat_message_id == 200
    assert msg.content_type == ContentType.TEXT
    assert msg.file_id is None


def test_message_with_media():
    """Test Message model with media content"""
    msg = Message(
        id=1,
        ticket_id=1,
        user_chat_message_id=100,
        support_chat_message_id=200,
        is_from_user=True,
        content_type=ContentType.PHOTO,
        text="",
        file_id="AgACAgIAAxkBAAI...",
    )
    assert msg.content_type == ContentType.PHOTO
    assert msg.file_id == "AgACAgIAAxkBAAI..."
    assert msg.text == ""


def test_message_sticker_empty_text():
    """Test that sticker messages have empty text"""
    msg = Message(
        id=1,
        ticket_id=1,
        user_chat_message_id=100,
        is_from_user=True,
        content_type=ContentType.STICKER,
        text="",
        file_id="CAACAgIAAxkBAAI...",
    )
    assert msg.text == ""
    assert msg.content_type == ContentType.STICKER


def test_pending_message_with_media():
    """Test PendingMessage with media content"""
    pending = PendingMessage(
        id=1,
        user_id=123,
        content_type=ContentType.PHOTO,
        text="",
        file_id="AgACAgIAAxkBAAI...",
        telegram_message_id=100,
    )
    assert pending.content_type == ContentType.PHOTO
    assert pending.file_id is not None
