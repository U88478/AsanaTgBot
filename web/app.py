import logging

import requests
from flask import Flask, request, render_template
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.config import *
from utils.token_encryption import encrypt_tokens

app = Flask('AsanaBotQ')


@app.route('/asana_redirect')
def asana_redirect_handler():
    code = request.args.get('code')
    logging.debug(request.json)
    if code:
        response = requests.post(
            'https://app.asana.com/-/oauth_token',
            data={
                'grant_type': 'authorization_code',
                'client_id': asana_client_id,
                'client_secret': asana_client_secret,
                'redirect_uri': redirect_url,
                'code': code
            }
        )

        if response.ok:
            # Отримання токенів
            tokens_data = response.json()
            access_token = tokens_data.get('access_token')
            refresh_token = tokens_data.get('refresh_token')

            # Шифрування обох токенів разом
            encrypted_tokens = encrypt_tokens(key, access_token, refresh_token)
            return render_template('index.html', encrypted_tokens=encrypted_tokens)
        else:
            return f"Error fetching access token: {response.text}", 500
    else:
        return "No code provided by Asana", 400


if __name__ == '__main__':
    app.run(port=5000)
