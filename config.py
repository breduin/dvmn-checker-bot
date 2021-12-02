"""Configiration for telegram bot."""
import os


DVMN_TOKEN = os.environ['DVMN_TOKEN']  # Ключ dvmn.org
TG_TOKEN = os.environ['TG_TOKEN']  # Ключ API Telegram
CHAT_ID = os.environ['CHAT_ID']  # ID пользователя Telegram

HEADERS = {
  'Authorization': f'Token {DVMN_TOKEN}'
  }

URL = 'https://dvmn.org/api/long_polling/'

# Время в сек., в течение которого бот ожидает ответ сервера dvmn.org
TIMEOUT = 90

# Пауза в сек. между попытками бота подключиться к серверу dvmn.org
CONNECTION_RETRY_WAITING_TIME = 60


class LogsOutput:
    """Open/close logs output directions."""
    FILE = False
    STREAM = False
    BOT = True
