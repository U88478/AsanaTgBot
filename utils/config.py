import os


token = '6886248036:AAHb4o7QNbLQ9cP89_8s6TDHaw8M-Y85w1g'
# pat_token = '2/1206070630058470/1206071134750827:a1bdfe76340c4edc3f12668d9bbae019'
redirect_url = 'https://asana-tg-bot-d40465f07121.herokuapp.com/asana_redirect'
asana_client_id = 1206188255229345
asana_client_secret = '22fc4708be564e39af7b34bf0f7bc410'
auth_url = f'https://app.asana.com/-/oauth_authorize?client_id={asana_client_id}&response_type=code&redirect_uri={redirect_url}&scope=default'
url = 'https://app.asana.com/'
key = 'c8OHE_EXWAmD8yxqbMrJLrGnVfMveROTKy9gq-ocAI0='
# db_url = 'sqlite:///AsanaDB.db'
db_url = os.getenv('DATABASE_URL')
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://')
