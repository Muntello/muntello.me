import pytest
from datetime import datetime
from app.models import User, Ticket, Message, PendingMessage, TicketStatus

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
