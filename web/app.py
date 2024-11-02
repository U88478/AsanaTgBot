import logging
import os
import sys

import requests
from flask import Flask, request, render_template

# Add parent directory to the path to import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.config import asana_client_id, asana_client_secret, redirect_url, key
from utils.token_encryption import encrypt_tokens

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask('AsanaBotQ')


@app.route('/asana_redirect')
def asana_redirect_handler():
    code = request.args.get('code')
    logging.debug(f"Received request with args: {request.args}")

    if code:
        response = requests.post(
            'https://app.asana.com/-/oauth_token',
            data={
                'grant_type': 'authorization_code',
                'client_id': asana_client_id,
                'client_secret': asana_client_secret,
                'redirect_uri': redirect_url,
                'code': code
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'}  # Ensure the correct Content-Type header
        )

        if response.ok:
            # Get tokens
            tokens_data = response.json()
            access_token = tokens_data.get('access_token')
            refresh_token = tokens_data.get('refresh_token')

            # Encrypt both tokens together
            encrypted_tokens = encrypt_tokens(key, access_token, refresh_token)
            return render_template('index.html', encrypted_tokens=encrypted_tokens)
        else:
            logging.error(f"Error fetching access token: {response.text}")
            return f"Error fetching access token: {response.text}", 500
    else:
        logging.warning("No code provided by Asana")
        return "No code provided by Asana", 400


if __name__ == '__main__':
    app.run(port=5000)
