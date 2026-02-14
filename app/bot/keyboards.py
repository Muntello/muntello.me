"""Telegram bot keyboard utilities."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_ticket_choice_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    """Create inline keyboard for ticket actions.

    Args:
        ticket_id: The ticket ID to attach to callback data

    Returns:
        InlineKeyboardMarkup with close and assign buttons
    """
    keyboard = [
        [
            InlineKeyboardButton("Close", callback_data=f"close_{ticket_id}"),
            InlineKeyboardButton("Assign to Me", callback_data=f"assign_{ticket_id}"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
