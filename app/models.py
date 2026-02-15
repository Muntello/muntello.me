from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
from enum import Enum


Base = declarative_base()


class TicketStatus(str, Enum):
    """Ticket status enum"""
    OPEN = "open"
    WAITING_SUPPORT = "waiting_support"
    WAITING_USER = "waiting_user"
    CLOSED = "closed"


class ContentType(str, Enum):
    """Message content type enum"""
    TEXT = "text"
    PHOTO = "photo"
    VIDEO = "video"
    VOICE = "voice"
    VIDEO_NOTE = "video_note"
    STICKER = "sticker"
    DOCUMENT = "document"
    ANIMATION = "animation"
    AUDIO = "audio"


class User(Base):
    """Telegram user model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)  # Telegram user_id
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_blocked = Column(Boolean, default=False, nullable=False)

    tickets = relationship("Ticket", back_populates="user")

    def __init__(self, **kwargs):
        """Initialize user with defaults"""
        if 'is_blocked' not in kwargs:
            kwargs['is_blocked'] = False
        super().__init__(**kwargs)


class Ticket(Base):
    """Support ticket model"""
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(20), default=TicketStatus.OPEN, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    closed_at = Column(DateTime, nullable=True)
    closed_by = Column(String(20), nullable=True)  # "staff", "auto", "user"
    reopened_at = Column(DateTime, nullable=True)

    # ID сообщения-треда в чате сотрудников
    support_thread_id = Column(Integer, nullable=True)

    user = relationship("User", back_populates="tickets")
    messages = relationship("Message", back_populates="ticket", cascade="all, delete-orphan")


class Message(Base):
    """Message in ticket"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)

    # Dual message IDs: track message in both chats
    user_chat_message_id = Column(Integer, nullable=True)
    support_chat_message_id = Column(Integer, nullable=True)

    is_from_user = Column(Boolean, default=True, nullable=False)

    # Content fields
    content_type = Column(String(20), default=ContentType.TEXT, nullable=False)
    text = Column(Text, nullable=True)
    file_id = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    ticket = relationship("Ticket", back_populates="messages")


class PendingMessage(Base):
    """Temporary storage for messages without ticket"""
    __tablename__ = "pending_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Content fields
    content_type = Column(String(20), default=ContentType.TEXT, nullable=False)
    text = Column(Text, nullable=True)
    file_id = Column(String(255), nullable=True)

    telegram_message_id = Column(Integer, nullable=False)
    support_notification_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
