from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.bot.filters import SupportChatFilter, PrivateChatFilter
from app.bot.keyboards import get_ticket_choice_keyboard
from app.services import ticket_service
from app.models import TicketStatus
import logging


logger = logging.getLogger(__name__)
router = Router()


@router.message(PrivateChatFilter())
async def handle_user_message(message: Message, session: AsyncSession):
    """Handle messages from users in private chat"""
    logger.info("user_message_received", extra={"user_id": message.from_user.id})

    # Get or create user
    user = await ticket_service.get_or_create_user(session, message.from_user)

    # Check for active ticket
    active_ticket = await ticket_service.get_active_ticket(session, user.id)

    if active_ticket:
        # Continue existing ticket
        await ticket_service.add_message_to_ticket(
            session,
            active_ticket,
            message.text,
            message.message_id,
            is_from_user=True
        )

        # Send to support chat
        support_msg = await message.bot.send_message(
            chat_id=settings.SUPPORT_CHAT_ID,
            text=(
                f"📩 Обращение #{active_ticket.id} | Статус: Ждет ответа\n\n"
                f"👤 {user.first_name}"
                f"{' @' + user.username if user.username else ''}\n"
                f"💬 {message.text}\n\n"
                f"---\nКоманды: /close - закрыть обращение"
            ),
            reply_to_message_id=active_ticket.support_thread_id
        )

        logger.info("message_forwarded_to_support", extra={
            "ticket_id": active_ticket.id,
            "user_id": user.id
        })
    else:
        # No active ticket, check for closed tickets
        last_closed = await ticket_service.get_last_closed_ticket(session, user.id)

        if last_closed:
            # Create pending message and ask support staff
            pending = await ticket_service.create_pending_message(
                session,
                user.id,
                message.text,
                message.message_id
            )

            keyboard = get_ticket_choice_keyboard(user.id, last_closed.id, pending.id)

            support_msg = await message.bot.send_message(
                chat_id=settings.SUPPORT_CHAT_ID,
                text=(
                    f"📩 Новое сообщение от пользователя\n"
                    f"👤 {user.first_name}"
                    f"{' @' + user.username if user.username else ''}\n"
                    f"📊 Последнее обращение: #{last_closed.id} "
                    f"(закрыто)\n\n"
                    f"💬 {message.text}"
                ),
                reply_markup=keyboard
            )

            # Update pending with notification ID
            pending.support_notification_id = support_msg.message_id
            await session.commit()

            logger.info("pending_message_created", extra={
                "pending_id": pending.id,
                "user_id": user.id,
                "last_ticket_id": last_closed.id
            })
        else:
            # First message from user - create new ticket
            ticket = await ticket_service.create_ticket(session, user.id)
            await ticket_service.add_message_to_ticket(
                session,
                ticket,
                message.text,
                message.message_id,
                is_from_user=True
            )

            # Send to support chat
            support_msg = await message.bot.send_message(
                chat_id=settings.SUPPORT_CHAT_ID,
                text=(
                    f"📩 Обращение #{ticket.id} | Статус: Ждет ответа\n\n"
                    f"👤 {user.first_name}"
                    f"{' @' + user.username if user.username else ''}\n"
                    f"💬 {message.text}\n\n"
                    f"---\nКоманды: /close - закрыть обращение"
                )
            )

            # Save thread ID
            ticket.support_thread_id = support_msg.message_id
            await session.commit()

            logger.info("new_ticket_created", extra={
                "ticket_id": ticket.id,
                "user_id": user.id
            })


@router.message(SupportChatFilter(), F.reply_to_message)
async def handle_support_reply(message: Message, session: AsyncSession):
    """Handle replies from support staff"""
    logger.info("support_reply_received", extra={
        "reply_to_message_id": message.reply_to_message.message_id
    })

    # Find ticket by support thread ID
    ticket = await ticket_service.get_ticket_by_support_thread_id(
        session,
        message.reply_to_message.message_id
    )

    if not ticket:
        await message.reply("⚠️ Не найдено обращение для этого сообщения")
        return

    # Check for /close command
    if message.text and message.text.startswith("/close"):
        await ticket_service.close_ticket(session, ticket, closed_by="staff")

        # Notify user
        await message.bot.send_message(
            ticket.user_id,
            f"✅ Ваше обращение #{ticket.id} закрыто. "
            f"Если нужна помощь - напишите снова!"
        )

        await message.reply(f"✅ Обращение #{ticket.id} закрыто")
        logger.info("ticket_closed_by_staff", extra={"ticket_id": ticket.id})
        return

    # Regular reply - add message and send to user
    await ticket_service.add_message_to_ticket(
        session,
        ticket,
        message.text,
        message.message_id,
        is_from_user=False
    )

    # Send to user
    await message.bot.send_message(ticket.user_id, message.text)

    logger.info("reply_sent_to_user", extra={
        "ticket_id": ticket.id,
        "user_id": ticket.user_id
    })


@router.callback_query(F.data.startswith("new_ticket:"))
async def handle_new_ticket_callback(callback: CallbackQuery, session: AsyncSession):
    """Handle new ticket creation from pending message"""
    _, user_id, pending_id = callback.data.split(":")

    pending = await ticket_service.get_pending_message(session, int(pending_id))
    if not pending:
        await callback.answer("❌ Сообщение не найдено")
        return

    # Create new ticket
    ticket = await ticket_service.create_ticket(session, int(user_id))
    await ticket_service.add_message_to_ticket(
        session,
        ticket,
        pending.text,
        pending.telegram_message_id,
        is_from_user=True
    )

    # Update support message
    user = await ticket_service.get_or_create_user(
        session,
        await callback.bot.get_chat(int(user_id))
    )

    await callback.message.edit_text(
        f"📩 Обращение #{ticket.id} | Статус: Ждет ответа\n\n"
        f"👤 {user.first_name}"
        f"{' @' + user.username if user.username else ''}\n"
        f"💬 {pending.text}\n\n"
        f"---\nКоманды: /close - закрыть обращение"
    )

    # Save thread ID
    ticket.support_thread_id = callback.message.message_id
    await session.commit()

    # Delete pending
    await ticket_service.delete_pending_message(session, pending.id)

    await callback.answer("✅ Создано новое обращение")
    logger.info("new_ticket_from_pending", extra={
        "ticket_id": ticket.id,
        "pending_id": pending.id
    })


@router.callback_query(F.data.startswith("reopen_ticket:"))
async def handle_reopen_ticket_callback(callback: CallbackQuery, session: AsyncSession):
    """Handle ticket reopen from pending message"""
    _, ticket_id, pending_id = callback.data.split(":")

    ticket = await ticket_service.get_ticket_by_id(session, int(ticket_id))
    pending = await ticket_service.get_pending_message(session, int(pending_id))

    if not ticket or not pending:
        await callback.answer("❌ Обращение или сообщение не найдено")
        return

    # Reopen ticket
    await ticket_service.reopen_ticket(session, ticket)
    await ticket_service.add_message_to_ticket(
        session,
        ticket,
        pending.text,
        pending.telegram_message_id,
        is_from_user=True
    )

    # Update support message
    user = await ticket_service.get_or_create_user(
        session,
        await callback.bot.get_chat(ticket.user_id)
    )

    await callback.message.edit_text(
        f"🔄 Обращение #{ticket.id} переоткрыто | Статус: Ждет ответа\n\n"
        f"👤 {user.first_name}"
        f"{' @' + user.username if user.username else ''}\n"
        f"💬 {pending.text}\n\n"
        f"---\nКоманды: /close - закрыть обращение"
    )

    # Delete pending
    await ticket_service.delete_pending_message(session, pending.id)

    await callback.answer("✅ Обращение переоткрыто")
    logger.info("ticket_reopened_from_pending", extra={
        "ticket_id": ticket.id,
        "pending_id": pending.id
    })


def setup_handlers(dp):
    """Setup all handlers"""
    dp.include_router(router)
