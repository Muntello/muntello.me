"""Content extraction and sending helpers for multi-media message support."""

from aiogram.types import Message as TgMessage
from aiogram import Bot
from app.models import ContentType
from app.config import settings
import logging

logger = logging.getLogger(__name__)


def extract_content(message: TgMessage) -> dict:
    """Extract content_type, text, and file_id from any Telegram message.

    For photos, takes the largest resolution (last element).
    For media without text (sticker, voice, video_note), text is "".
    """
    if message.photo:
        return {
            "content_type": ContentType.PHOTO,
            "text": message.caption or "",
            "file_id": message.photo[-1].file_id,
        }
    if message.video:
        return {
            "content_type": ContentType.VIDEO,
            "text": message.caption or "",
            "file_id": message.video.file_id,
        }
    if message.animation:
        return {
            "content_type": ContentType.ANIMATION,
            "text": message.caption or "",
            "file_id": message.animation.file_id,
        }
    if message.document:
        return {
            "content_type": ContentType.DOCUMENT,
            "text": message.caption or "",
            "file_id": message.document.file_id,
        }
    if message.voice:
        return {
            "content_type": ContentType.VOICE,
            "text": "",
            "file_id": message.voice.file_id,
        }
    if message.video_note:
        return {
            "content_type": ContentType.VIDEO_NOTE,
            "text": "",
            "file_id": message.video_note.file_id,
        }
    if message.sticker:
        return {
            "content_type": ContentType.STICKER,
            "text": "",
            "file_id": message.sticker.file_id,
        }
    if message.audio:
        return {
            "content_type": ContentType.AUDIO,
            "text": message.caption or "",
            "file_id": message.audio.file_id,
        }
    # Default: text message
    return {
        "content_type": ContentType.TEXT,
        "text": message.text or "",
        "file_id": None,
    }


def build_header(
    ticket_id: int,
    user_first_name: str,
    username: str | None,
    status_text: str = "Ждет ответа",
) -> str:
    """Build the standard ticket header for support chat messages."""
    return (
        f"📩 Обращение #{ticket_id} | Статус: {status_text}\n\n"
        f"👤 {user_first_name}"
        f"{' @' + username if username else ''}\n"
    )


async def send_user_message_to_support(
    bot: Bot,
    message: TgMessage,
    ticket,
    user_first_name: str,
    username: str | None,
    content: dict,
    is_first_message: bool = False,
) -> int:
    """Forward a user's message to the support chat, preserving media.

    Text: sends formatted header + text as one message.
    Media + first_message: text header first (becomes support_thread_id),
        then copy_message as reply.
    Media + not first: copy_message as reply to thread.

    Returns support_chat_message_id.
    """
    if content["content_type"] == ContentType.TEXT:
        body = (
            build_header(ticket.id, user_first_name, username)
            + f"💬 {content['text']}\n\n"
            + "---\nКоманды: /close - закрыть обращение"
        )
        support_msg = await bot.send_message(
            chat_id=settings.SUPPORT_CHAT_ID,
            text=body,
            reply_to_message_id=ticket.support_thread_id if not is_first_message else None,
        )
        return support_msg.message_id

    # Media message
    if is_first_message:
        # Send text header first — it becomes the thread anchor
        header_text = (
            build_header(ticket.id, user_first_name, username)
            + f"📎 [{content['content_type'].value}]\n\n"
            + "---\nКоманды: /close - закрыть обращение"
        )
        header_msg = await bot.send_message(
            chat_id=settings.SUPPORT_CHAT_ID,
            text=header_text,
        )
        ticket.support_thread_id = header_msg.message_id

        copied = await bot.copy_message(
            chat_id=settings.SUPPORT_CHAT_ID,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
            reply_to_message_id=header_msg.message_id,
        )
        return copied.message_id

    # Subsequent media message: copy as reply to thread
    copied = await bot.copy_message(
        chat_id=settings.SUPPORT_CHAT_ID,
        from_chat_id=message.chat.id,
        message_id=message.message_id,
        reply_to_message_id=ticket.support_thread_id,
    )
    return copied.message_id


async def send_support_reply_to_user(
    bot: Bot,
    message: TgMessage,
    user_id: int,
) -> int:
    """Forward support staff reply to user via copy_message.

    Preserves all content types and formatting.
    Returns user_chat_message_id.
    """
    copied = await bot.copy_message(
        chat_id=user_id,
        from_chat_id=message.chat.id,
        message_id=message.message_id,
    )
    return copied.message_id
