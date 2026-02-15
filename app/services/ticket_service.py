from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from aiogram.types import User as TgUser
from app.models import User, Ticket, Message, PendingMessage, TicketStatus, ContentType
from datetime import datetime
import logging


logger = logging.getLogger(__name__)


async def get_or_create_user(session: AsyncSession, tg_user: TgUser) -> User:
    """Get existing user or create new one"""
    result = await session.execute(
        select(User).where(User.id == tg_user.id)
    )
    user = result.scalar_one_or_none()

    if user:
        # Update last activity and user info
        user.last_activity = datetime.utcnow()
        user.username = tg_user.username
        user.first_name = tg_user.first_name
        user.last_name = tg_user.last_name
    else:
        # Create new user
        user = User(
            id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name
        )
        session.add(user)

    await session.commit()
    await session.refresh(user)
    return user


async def get_active_ticket(session: AsyncSession, user_id: int) -> Ticket | None:
    """Get active ticket for user (status != closed)"""
    result = await session.execute(
        select(Ticket).where(
            and_(
                Ticket.user_id == user_id,
                Ticket.status != TicketStatus.CLOSED
            )
        ).order_by(Ticket.created_at.desc())
    )
    return result.scalar_one_or_none()


async def get_last_closed_ticket(session: AsyncSession, user_id: int) -> Ticket | None:
    """Get last closed ticket for user"""
    result = await session.execute(
        select(Ticket).where(
            and_(
                Ticket.user_id == user_id,
                Ticket.status == TicketStatus.CLOSED
            )
        ).order_by(Ticket.closed_at.desc())
    )
    return result.scalar_one_or_none()


async def create_ticket(session: AsyncSession, user_id: int) -> Ticket:
    """Create new ticket for user"""
    ticket = Ticket(
        user_id=user_id,
        status=TicketStatus.WAITING_SUPPORT
    )
    session.add(ticket)
    await session.commit()
    await session.refresh(ticket)

    logger.info("ticket_created", extra={"ticket_id": ticket.id, "user_id": user_id})
    return ticket


async def add_message_to_ticket(
    session: AsyncSession,
    ticket: Ticket,
    content: dict,
    user_chat_message_id: int | None = None,
    support_chat_message_id: int | None = None,
    is_from_user: bool = True,
) -> Message:
    """Add message to ticket with content metadata.

    Args:
        content: dict from extract_content() with keys:
                 content_type, text, file_id
    """
    message = Message(
        ticket_id=ticket.id,
        user_chat_message_id=user_chat_message_id,
        support_chat_message_id=support_chat_message_id,
        is_from_user=is_from_user,
        content_type=content["content_type"],
        text=content.get("text") or "",
        file_id=content.get("file_id"),
    )
    session.add(message)

    if is_from_user:
        ticket.status = TicketStatus.WAITING_SUPPORT
    else:
        ticket.status = TicketStatus.WAITING_USER

    ticket.updated_at = datetime.utcnow()

    await session.commit()
    await session.refresh(message)
    return message


async def close_ticket(
    session: AsyncSession,
    ticket: Ticket,
    closed_by: str = "staff"
) -> Ticket:
    """Close ticket"""
    ticket.status = TicketStatus.CLOSED
    ticket.closed_at = datetime.utcnow()
    ticket.closed_by = closed_by

    await session.commit()
    await session.refresh(ticket)

    logger.info("ticket_closed", extra={"ticket_id": ticket.id, "closed_by": closed_by})
    return ticket


async def reopen_ticket(session: AsyncSession, ticket: Ticket) -> Ticket:
    """Reopen closed ticket"""
    ticket.status = TicketStatus.WAITING_SUPPORT
    ticket.reopened_at = datetime.utcnow()
    ticket.closed_at = None
    ticket.closed_by = None

    await session.commit()
    await session.refresh(ticket)

    logger.info("ticket_reopened", extra={"ticket_id": ticket.id})
    return ticket


async def create_pending_message(
    session: AsyncSession,
    user_id: int,
    content: dict,
    telegram_message_id: int,
    support_notification_id: int | None = None,
) -> PendingMessage:
    """Create pending message with content metadata."""
    pending = PendingMessage(
        user_id=user_id,
        content_type=content["content_type"],
        text=content.get("text") or "",
        file_id=content.get("file_id"),
        telegram_message_id=telegram_message_id,
        support_notification_id=support_notification_id,
    )
    session.add(pending)
    await session.commit()
    await session.refresh(pending)
    return pending


async def get_pending_message(session: AsyncSession, pending_id: int) -> PendingMessage | None:
    """Get pending message by ID"""
    result = await session.execute(
        select(PendingMessage).where(PendingMessage.id == pending_id)
    )
    return result.scalar_one_or_none()


async def delete_pending_message(session: AsyncSession, pending_id: int):
    """Delete pending message"""
    result = await session.execute(
        select(PendingMessage).where(PendingMessage.id == pending_id)
    )
    pending = result.scalar_one_or_none()
    if pending:
        await session.delete(pending)
        await session.commit()


async def get_ticket_by_id(session: AsyncSession, ticket_id: int) -> Ticket | None:
    """Get ticket by ID"""
    result = await session.execute(
        select(Ticket).where(Ticket.id == ticket_id)
    )
    return result.scalar_one_or_none()


async def get_ticket_by_support_thread_id(
    session: AsyncSession,
    support_thread_id: int
) -> Ticket | None:
    """Get ticket by support thread message ID"""
    result = await session.execute(
        select(Ticket).where(Ticket.support_thread_id == support_thread_id)
    )
    return result.scalar_one_or_none()


async def get_ticket_by_support_message_id(
    session: AsyncSession,
    support_message_id: int,
) -> Ticket | None:
    """Find ticket by any message ID in the support chat.

    Looks up Message.support_chat_message_id to find which ticket
    a given support chat message belongs to. This enables replying
    to ANY message in the thread, not just the first one.
    """
    result = await session.execute(
        select(Message).where(
            Message.support_chat_message_id == support_message_id
        )
    )
    msg = result.scalar_one_or_none()
    if msg:
        ticket_result = await session.execute(
            select(Ticket).where(Ticket.id == msg.ticket_id)
        )
        return ticket_result.scalar_one_or_none()
    return None
