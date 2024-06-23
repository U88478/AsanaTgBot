import asana
from asana.rest import ApiException
import requests

from db.functions import *
from utils.config import *


def get_asana_id(asana_token):
    asana_id = 0
    headers = {
        'Authorization': 'Bearer ' + asana_token
    }
    response = requests.get(url + 'api/1.0/users/me', headers=headers)
    if response.ok:
        user_data = response.json()
        asana_id = user_data['data']['gid']
    else:
        print("Error:", response.text)
    return asana_id


def get_asana_client(tg_id):
    user = get_user(tg_id)
    if user is None:
        return None

    try:
        configuration = asana.Configuration()
        configuration.access_token = user.asana_token
        asana_client = asana.ApiClient(configuration)
        workspaces = asana.WorkspacesApi(asana_client).get_workspaces({'opt_fields': 'name'})
        _ = {workspace['name']: workspace['gid'] for workspace in workspaces}
        return asana_client
    except ApiException as e:
        if e.status == 401:
            # Оновлення токена
            new_access_token, new_refresh_token = refresh_access_token(user.asana_refresh_token)
            # Оновлення даних користувача
            create_user(tg_id, user.tg_first_name, user.tg_username, new_access_token, new_refresh_token,
                                user.asana_id)
            # Повторне створення клієнта Asana з новим токеном
            configuration.access_token = new_access_token
            return asana.ApiClient(configuration)
        else:
            raise e


def refresh_access_token(refresh_token):
    token_url = "https://app.asana.com/-/oauth_token"
    payload = {
        'grant_type': 'refresh_token',
        'client_id': asana_client_id,
        'client_secret': asana_client_secret,
        'refresh_token': refresh_token
    }
    response = requests.post(token_url, data=payload)
    if response.status_code == 200:
        new_tokens = response.json()
        new_access_token = new_tokens['access_token']
        new_refresh_token = new_tokens.get('refresh_token', refresh_token)
        return new_access_token, new_refresh_token
    else:
        raise Exception("Не вдалося оновити токен: " + response.text)