from utils.asana_functions import refresh_access_token, get_asana_client
import asana
from asana.rest import ApiException
from functools import wraps
from db.functions import get_user, create_user


def refresh_token(func):
    @wraps(func)
    async def wrapper(message, *args, **kwargs):
        user = get_user(message.from_user.id)
        asana_client = get_asana_client(message.from_user.id)
        users_api_instance = asana.UsersApi(asana_client)
        opts = {

        }
        try:
            users_api_instance.get_user("me", opts)
        except ApiException:
            new_access_token, new_refresh_token = refresh_access_token(user.asana_refresh_token)
            create_user(message.from_user.id, message.from_user.first_name, 
                        message.from_user.username, new_access_token, 
                        new_refresh_token, user.asana_id)
            return
        return await func(message, *args, **kwargs)
    return wrapper
