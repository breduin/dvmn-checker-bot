import os

from environs import Env


env = Env()
env.read_env()

DVMN_TOKEN = env.str('DVMN_TOKEN')
TG_TOKEN = env.str('TG_TOKEN')
CHAT_ID = env('CHAT_ID')

HEADERS = {
  'Authorization': f'Token {DVMN_TOKEN}'
  }

URL = 'https://dvmn.org/api/long_polling/'

TIMEOUT = 90

CONNECTION_RETRY_WAITING_TIME = 60



