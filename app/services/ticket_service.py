from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from aiogram.types import User as TgUser
from app.models import User, Ticket, Message, PendingMessage, TicketStatus
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
    text: str,
    telegram_message_id: int,
    is_from_user: bool = True
) -> Message:
    """Add message to ticket"""
    message = Message(
        ticket_id=ticket.id,
        telegram_message_id=telegram_message_id,
        text=text,
        is_from_user=is_from_user
    )
    session.add(message)

    # Update ticket status
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
    text: str,
    telegram_message_id: int,
    support_notification_id: int | None = None
) -> PendingMessage:
    """Create pending message"""
    pending = PendingMessage(
        user_id=user_id,
        text=text,
        telegram_message_id=telegram_message_id,
        support_notification_id=support_notification_id
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
