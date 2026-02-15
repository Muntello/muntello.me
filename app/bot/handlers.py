from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.bot.filters import SupportChatFilter, PrivateChatFilter
from app.bot.keyboards import get_ticket_choice_keyboard
from app.bot.content import (
    extract_content,
    build_header,
    send_user_message_to_support,
    send_support_reply_to_user,
)
from app.services import ticket_service
from app.models import TicketStatus, ContentType
import logging


logger = logging.getLogger(__name__)
router = Router()


@router.message(PrivateChatFilter())
async def handle_user_message(message: Message, session: AsyncSession):
    """Handle messages from users in private chat (text and media)"""
    logger.info("user_message_received", extra={
        "user_id": message.from_user.id,
        "content_type": message.content_type,
    })

    user = await ticket_service.get_or_create_user(session, message.from_user)
    content = extract_content(message)

    active_ticket = await ticket_service.get_active_ticket(session, user.id)

    if active_ticket:
        # Forward to support chat
        support_msg_id = await send_user_message_to_support(
            bot=message.bot,
            message=message,
            ticket=active_ticket,
            user_first_name=user.first_name,
            username=user.username,
            content=content,
        )

        await ticket_service.add_message_to_ticket(
            session,
            active_ticket,
            content=content,
            user_chat_message_id=message.message_id,
            support_chat_message_id=support_msg_id,
            is_from_user=True,
        )

        logger.info("message_forwarded_to_support", extra={
            "ticket_id": active_ticket.id,
            "user_id": user.id,
            "content_type": content["content_type"].value,
        })
    else:
        last_closed = await ticket_service.get_last_closed_ticket(session, user.id)

        if last_closed:
            # Pending message flow
            pending = await ticket_service.create_pending_message(
                session,
                user.id,
                content=content,
                telegram_message_id=message.message_id,
            )

            keyboard = get_ticket_choice_keyboard(user.id, last_closed.id, pending.id)

            # Build notification text with content type indicator
            display_text = content["text"] or ""
            type_indicator = ""
            if content["content_type"] != ContentType.TEXT:
                type_indicator = f"📎 [{content['content_type'].value}] "

            support_msg = await message.bot.send_message(
                chat_id=settings.SUPPORT_CHAT_ID,
                text=(
                    f"📩 Новое сообщение от пользователя\n"
                    f"👤 {user.first_name}"
                    f"{' @' + user.username if user.username else ''}\n"
                    f"📊 Последнее обращение: #{last_closed.id} "
                    f"(закрыто)\n\n"
                    f"{type_indicator}💬 {display_text}"
                ),
                reply_markup=keyboard,
            )

            pending.support_notification_id = support_msg.message_id
            await session.commit()

            logger.info("pending_message_created", extra={
                "pending_id": pending.id,
                "user_id": user.id,
                "last_ticket_id": last_closed.id,
                "content_type": content["content_type"].value,
            })
        else:
            # First message from user — create new ticket
            ticket = await ticket_service.create_ticket(session, user.id)

            support_msg_id = await send_user_message_to_support(
                bot=message.bot,
                message=message,
                ticket=ticket,
                user_first_name=user.first_name,
                username=user.username,
                content=content,
                is_first_message=True,
            )

            # For text, the formatted message IS the thread anchor
            if content["content_type"] == ContentType.TEXT:
                ticket.support_thread_id = support_msg_id

            await ticket_service.add_message_to_ticket(
                session,
                ticket,
                content=content,
                user_chat_message_id=message.message_id,
                support_chat_message_id=support_msg_id,
                is_from_user=True,
            )
            await session.commit()

            logger.info("new_ticket_created", extra={
                "ticket_id": ticket.id,
                "user_id": user.id,
                "content_type": content["content_type"].value,
            })


@router.message(SupportChatFilter(), F.reply_to_message)
async def handle_support_reply(message: Message, session: AsyncSession):
    """Handle replies from support staff (text and media)"""
    reply_to_id = message.reply_to_message.message_id

    logger.info("support_reply_received", extra={
        "reply_to_message_id": reply_to_id,
        "content_type": message.content_type,
    })

    # Two-step lookup: specific message first, then thread header fallback
    ticket = await ticket_service.get_ticket_by_support_message_id(
        session, reply_to_id
    )
    if not ticket:
        ticket = await ticket_service.get_ticket_by_support_thread_id(
            session, reply_to_id
        )

    if not ticket:
        await message.reply("⚠️ Не найдено обращение для этого сообщения")
        return

    # /close works only as a text command
    if message.text and message.text.strip().startswith("/close"):
        await ticket_service.close_ticket(session, ticket, closed_by="staff")

        await message.bot.send_message(
            ticket.user_id,
            f"✅ Ваше обращение #{ticket.id} закрыто. "
            f"Если нужна помощь - напишите снова!",
        )

        await message.reply(f"✅ Обращение #{ticket.id} закрыто")
        logger.info("ticket_closed_by_staff", extra={"ticket_id": ticket.id})
        return

    # Forward reply to user (preserves all content types)
    user_msg_id = await send_support_reply_to_user(
        bot=message.bot,
        message=message,
        user_id=ticket.user_id,
    )

    content = extract_content(message)

    await ticket_service.add_message_to_ticket(
        session,
        ticket,
        content=content,
        user_chat_message_id=user_msg_id,
        support_chat_message_id=message.message_id,
        is_from_user=False,
    )

    logger.info("reply_sent_to_user", extra={
        "ticket_id": ticket.id,
        "user_id": ticket.user_id,
        "content_type": content["content_type"].value,
    })


@router.callback_query(F.data.startswith("new_ticket:"))
async def handle_new_ticket_callback(callback: CallbackQuery, session: AsyncSession):
    """Handle new ticket creation from pending message"""
    _, user_id, pending_id = callback.data.split(":")

    pending = await ticket_service.get_pending_message(session, int(pending_id))
    if not pending:
        await callback.answer("❌ Сообщение не найдено")
        return

    user = await ticket_service.get_or_create_user(
        session,
        await callback.bot.get_chat(int(user_id)),
    )

    ticket = await ticket_service.create_ticket(session, int(user_id))

    # Build content dict from pending message fields
    pending_content = {
        "content_type": pending.content_type,
        "text": pending.text or "",
        "file_id": pending.file_id,
    }

    display_text = pending.text or ""
    type_indicator = ""
    if pending.content_type != ContentType.TEXT:
        type_indicator = f"📎 [{pending.content_type}] "

    await callback.message.edit_text(
        build_header(ticket.id, user.first_name, user.username)
        + f"{type_indicator}💬 {display_text}\n\n"
        + "---\nКоманды: /close - закрыть обращение"
    )

    ticket.support_thread_id = callback.message.message_id

    # If media, try to copy to support chat as reply to thread
    support_msg_id = callback.message.message_id
    if pending.content_type != ContentType.TEXT and pending.file_id:
        try:
            copied = await callback.bot.copy_message(
                chat_id=settings.SUPPORT_CHAT_ID,
                from_chat_id=int(user_id),
                message_id=pending.telegram_message_id,
                reply_to_message_id=ticket.support_thread_id,
            )
            support_msg_id = copied.message_id
        except Exception as e:
            logger.warning("Could not copy media from pending: %s", e)

    await ticket_service.add_message_to_ticket(
        session,
        ticket,
        content=pending_content,
        user_chat_message_id=pending.telegram_message_id,
        support_chat_message_id=support_msg_id,
        is_from_user=True,
    )
    await session.commit()

    await ticket_service.delete_pending_message(session, pending.id)

    await callback.answer("✅ Создано новое обращение")
    logger.info("new_ticket_from_pending", extra={
        "ticket_id": ticket.id,
        "pending_id": pending.id,
        "content_type": pending.content_type,
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

    await ticket_service.reopen_ticket(session, ticket)

    user = await ticket_service.get_or_create_user(
        session,
        await callback.bot.get_chat(ticket.user_id),
    )

    pending_content = {
        "content_type": pending.content_type,
        "text": pending.text or "",
        "file_id": pending.file_id,
    }

    display_text = pending.text or ""
    type_indicator = ""
    if pending.content_type != ContentType.TEXT:
        type_indicator = f"📎 [{pending.content_type}] "

    await callback.message.edit_text(
        f"🔄 Обращение #{ticket.id} переоткрыто | Статус: Ждет ответа\n\n"
        f"👤 {user.first_name}"
        f"{' @' + user.username if user.username else ''}\n"
        f"{type_indicator}💬 {display_text}\n\n"
        f"---\nКоманды: /close - закрыть обращение"
    )

    # If media, try to copy to support chat
    support_msg_id = callback.message.message_id
    if pending.content_type != ContentType.TEXT and pending.file_id:
        try:
            copied = await callback.bot.copy_message(
                chat_id=settings.SUPPORT_CHAT_ID,
                from_chat_id=ticket.user_id,
                message_id=pending.telegram_message_id,
                reply_to_message_id=ticket.support_thread_id,
            )
            support_msg_id = copied.message_id
        except Exception as e:
            logger.warning("Could not copy media from pending: %s", e)

    await ticket_service.add_message_to_ticket(
        session,
        ticket,
        content=pending_content,
        user_chat_message_id=pending.telegram_message_id,
        support_chat_message_id=support_msg_id,
        is_from_user=True,
    )

    await ticket_service.delete_pending_message(session, pending.id)

    await callback.answer("✅ Обращение переоткрыто")
    logger.info("ticket_reopened_from_pending", extra={
        "ticket_id": ticket.id,
        "pending_id": pending.id,
        "content_type": pending.content_type,
    })


def setup_handlers(dp):
    """Setup all handlers"""
    dp.include_router(router)
