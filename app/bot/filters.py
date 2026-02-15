from aiogram.filters import BaseFilter
from aiogram.types import Message
from app.config import settings


class SupportChatFilter(BaseFilter):
    """Filter for messages in support chat (excludes bot's own messages)"""

    async def __call__(self, message: Message) -> bool:
        if message.chat.id != settings.SUPPORT_CHAT_ID:
            return False
        # Ignore bot's own messages to prevent processing loops
        if message.from_user and message.from_user.is_bot:
            return False
        return True


class PrivateChatFilter(BaseFilter):
    """Filter for private messages"""

    async def __call__(self, message: Message) -> bool:
        return message.chat.type == "private"
