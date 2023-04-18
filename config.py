import os

BOT_TOKEN = '6226006527:AAHj4YmD6x8yiLOxJclzCbZFUfn_htxNh8A'
GROUP_ID = -932963184

api_username = os.getenv('API_NAME')
api_password = os.getenv('API_PASS')
request_timeout_seconds = 10

callback_delay_seconds = 10

webhook_port = 8443
webhook_url = f'195.14.122.147:{webhook_port}/webtransaction'