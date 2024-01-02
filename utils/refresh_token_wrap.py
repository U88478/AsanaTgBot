from asana_functions import refresh_access_token
from functools import wraps
from db.functions import get_user, create_user


def refresh_token(func):
    @wraps(func)
    async def wrapper(message, *args, **kwargs):
        user = get_user(message.from_user.id)
        if user and refresh_access_token(user.asana_refresh_token):
            try:
                new_access_token, new_refresh_token = refresh_access_token(user.asana_refresh_token)
                create_user(message.from_user.id, message.from_user.first_name, 
                            message.from_user.username, new_access_token, 
                            new_refresh_token, user.asana_id)
            except Exception as e:
                await message.answer(f"Помилка оновлення токена: {e}")
                return
        return await func(message, *args, **kwargs)
    return wrapper
