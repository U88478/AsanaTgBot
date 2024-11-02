import logging

import asana
import requests
from asana.rest import ApiException

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
        logging.debug("Error:", response.text)
    return asana_id


def get_asana_client(user_id, token=None):
    user = get_user(user_id)
    if not user:
        return None

    if token:
        access_token = token
    else:
        access_token = user.asana_token

    # Initialize the Asana client with the access token
    configuration = asana.Configuration()
    configuration.access_token = access_token
    asana_client = asana.ApiClient(configuration)

    try:
        # Make a lightweight API call to verify the token
        asana.UsersApi(asana_client).get_user('me', opts={})
        return asana_client  # Token is valid, return the client
    except asana.rest.ApiException as e:
        if e.status == 401 and not token:  # Unauthorized, token may be expired or revoked
            try:
                # Attempt to refresh the token
                new_access_token, new_refresh_token = refresh_access_token(user.asana_refresh_token)

                # Update the user's token in the database
                create_user(
                    tg_id=user_id,
                    tg_first_name=user.tg_first_name,
                    tg_username=user.tg_username,
                    asana_token=new_access_token,
                    asana_refresh_token=new_refresh_token,
                    asana_id=user.asana_id
                )

                # Reinitialize the Asana client with the new token
                configuration.access_token = new_access_token
                asana_client = asana.ApiClient(configuration)

                # Test the new token with a lightweight API call
                asana.UsersApi(asana_client).get_user('me', opts={})
                return asana_client  # New token is valid
            except Exception:
                raise Exception(f"Failed to refresh token: {Exception}")
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
