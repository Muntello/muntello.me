from aiogram.filters import BaseFilter
from aiogram.types import Message
from app.config import settings


class SupportChatFilter(BaseFilter):
    """Filter for messages in support chat"""

    async def __call__(self, message: Message) -> bool:
        return message.chat.id == settings.SUPPORT_CHAT_ID


class PrivateChatFilter(BaseFilter):
    """Filter for private messages"""

    async def __call__(self, message: Message) -> bool:
        return message.chat.type == "private"
