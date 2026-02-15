from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_ticket_choice_keyboard(user_id: int, last_ticket_id: int, pending_id: int) -> InlineKeyboardMarkup:
    """
    Keyboard for choosing between new ticket or reopen.

    Args:
        user_id: Telegram user ID
        last_ticket_id: Last closed ticket ID
        pending_id: Pending message ID

    Returns:
        InlineKeyboardMarkup with choice buttons
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📝 Новое обращение",
                callback_data=f"new_ticket:{user_id}:{pending_id}"
            ),
            InlineKeyboardButton(
                text=f"🔄 Переоткрыть #{last_ticket_id}",
                callback_data=f"reopen_ticket:{last_ticket_id}:{pending_id}"
            )
        ]
    ])
    return keyboard
