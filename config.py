import os

BOT_TOKEN = ''
GROUP_ID = ''

api_username = os.getenv('API_NAME')
api_password = os.getenv('API_PASS')
request_timeout_seconds = 10

callback_delay_seconds = 10

webhook_port = 8443
webhook_url = f'1.1.1.1:{webhook_port}/webtransaction'
