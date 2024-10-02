from functools import wraps

from aiogram.types import Message

from db.functions import get_default_settings


def check_settings(func):
    @wraps(func)
    async def wrapper(message: Message, *args, **kwargs):
        settings = get_default_settings(message.chat.id)
        if not settings:
            return await message.reply(
                "Будь ласка, спочатку оберіть налаштування за допомогою команди /link в цьому чаті.")
        return await func(message, *args, **kwargs)

    return wrapper
