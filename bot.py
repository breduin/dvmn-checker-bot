"""
Telegram bot checking the lessons at DVMN site and reporting the result.
"""
import os
import sys
import requests
import telegram
import logging
from logging.handlers import RotatingFileHandler
from textwrap import dedent
from time import sleep


logger = logging.getLogger(__file__)


def get_parsed_answer(attempts: list) -> str:
    """Return answer from dvmn.org in human-readable form."""
    is_negative_text = {
        True: 'К сожалению, в работе нашлись ошибки.',
        False: 'Задание выполнено, можете приступать к следующему уроку.',
        }
    answer = ''
    for attempt in attempts:
        answer += f"""
        Проверена работа {attempt['lesson_title']}
        {is_negative_text[attempt['is_negative']]}
        Ссылка на задачу: {attempt['lesson_url']}
        """

    return dedent(answer)


def get_works():
    """Listen DVMN server and get reviewed works as soon as they appear."""
    # Время в сек., в течение которого бот ожидает ответ сервера dvmn.org
    TIMEOUT = 90

    # Пауза в сек. между попытками бота подключиться к серверу dvmn.org
    CONNECTION_RETRY_WAITING_TIME = 60

    # Заголовок запроса с ключом DVMN
    HEADERS = {
    'Authorization': f'Token {os.environ["DVMN_TOKEN"]}'
    }
    # URL для API DVMN
    URL = 'https://dvmn.org/api/long_polling/'

    request_params = {}

    while True:
        logger.debug('Sending request ...')
        try:
            response = requests.get(URL,
                                    headers=HEADERS,
                                    params=request_params,
                                    timeout=TIMEOUT,
                                    )
            response.raise_for_status()
        except requests.ReadTimeout:
            continue
        except requests.ConnectionError:
            logger.warning('No server connection.')
            sleep(CONNECTION_RETRY_WAITING_TIME)
            continue

        works = response.json()
        if works['status'] == 'timeout':
            request_params["timestamp"] = works["timestamp_to_request"]
            continue

        if works['status'] == 'found':
            logger.info('Found reviewed works.')
            request_params["timestamp"] = works["last_attempt_timestamp"]
            answer = get_parsed_answer(works['new_attempts'])
            logger.info(answer)


def main():
    """Application entry point."""

    # Ключ API Telegram
    TG_TOKEN = os.environ['TG_TOKEN']
    # ID пользователя Telegram
    CHAT_ID = os.environ['CHAT_ID']
    # Записывать логи в файл?
    FILE = (os.getenv('FILE', 'False') == 'True')
    # Выводить логи в терминал?
    STREAM = (os.getenv('STREAM', 'False') == 'True')
    # Выводить логи в телеграм-чат?
    BOT = (os.getenv('BOT', 'False') == 'True')

    class BotHandler(logging.Handler):

        bot = telegram.Bot(token=TG_TOKEN)

        def emit(self, record):
            log_entry = self.format(record)
            self.bot.send_message(chat_id=CHAT_ID, text=log_entry)

    # Set logging level.
    logger.setLevel(logging.DEBUG)

    if FILE:
        file_handler = RotatingFileHandler(
            'main.log',
            maxBytes=100000,
            backupCount=2
            )
        file_handler.setLevel(logging.INFO)
        file_handler_formatter = logging.Formatter(
            '%(asctime)s - line %(lineno)s - %(levelname)s - %(message)s'
            )
        file_handler.setFormatter(file_handler_formatter)
        logger.addHandler(file_handler)

    if STREAM:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.DEBUG)
        stream_formatter = logging.Formatter('%(asctime)s - %(message)s')
        stream_handler.setFormatter(stream_formatter)
        logger.addHandler(stream_handler)

    if BOT:
        bot_handler = BotHandler()
        bot_handler.setLevel(logging.INFO)
        bot_formatter = logging.Formatter('%(message)s')
        bot_handler.setFormatter(bot_formatter)
        logger.addHandler(bot_handler)

    logger.debug('Bot started.')
    logger.info('Program started.')
    
    get_works()

    logger.info('Program stopped.')


if __name__ == '__main__':

    try:
        main()
    except KeyboardInterrupt:
        logger.info('Program stopped.')
        exit()
    except Exception as e:
        logger.exception(e)
        raise e
