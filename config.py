import os


DVMN_TOKEN = os.environ['DVMN_TOKEN']
TG_TOKEN = os.environ['TG_TOKEN']
CHAT_ID = os.environ['CHAT_ID']

HEADERS = {
  'Authorization': f'Token {DVMN_TOKEN}'
  }

URL = 'https://dvmn.org/api/long_polling/'

TIMEOUT = 90

CONNECTION_RETRY_WAITING_TIME = 60



