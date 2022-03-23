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
from environs import Env


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
    env = Env()
    env.read_env()

    TG_TOKEN = env.str('TG_TOKEN')
    TG_CHAT_ID = env.str('TG_CHAT_ID')

    RESPONSE_WAITING_TIME = 90    
    CONNECTION_RETRY_WAITING_TIME = 60
    DVMN_REQUEST_HEADERS = {
    'Authorization': f'Token {env.str("DVMN_TOKEN")}'
    }
    DVMN_URL = 'https://dvmn.org/api/long_polling/'

    request_params = {}

    works_checking_bot = telegram.Bot(token=TG_TOKEN)

    while True:
        logger.debug('Sending request ...')
        try:
            response = requests.get(DVMN_URL,
                                    headers=DVMN_REQUEST_HEADERS,
                                    params=request_params,
                                    timeout=RESPONSE_WAITING_TIME,
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
            works_checking_bot.send_message(chat_id=TG_CHAT_ID, text=answer)


def main():
    """Application entry point."""

    env = Env()
    env.read_env()

    TG_TOKEN = env.str('TG_TOKEN')
    TG_CHAT_ID = env.str('TG_CHAT_ID')
    
    SAVE_LOGS_TO_FILE = env.bool('SAVE_LOGS_TO_FILE')
    SEND_LOGS_TO_STREAM = env.bool('SEND_LOGS_TO_STREAM')
    SEND_LOGS_TO_BOT = env.bool('SEND_LOGS_TO_BOT')

    logging_bot = telegram.Bot(token=TG_TOKEN)

    class BotHandler(logging.Handler):        

        def emit(self, record):
            log_entry = self.format(record)
            logging_bot.send_message(chat_id=TG_CHAT_ID, text=log_entry)

    logger.setLevel(logging.DEBUG)

    if SAVE_LOGS_TO_FILE:
        file_handler = RotatingFileHandler(
            'logs/main.log',
            maxBytes=100000,
            backupCount=2
            )
        file_handler.setLevel(logging.INFO)
        file_handler_formatter = logging.Formatter(
            '%(asctime)s - line %(lineno)s - %(levelname)s - %(message)s'
            )
        file_handler.setFormatter(file_handler_formatter)
        logger.addHandler(file_handler)

    if SEND_LOGS_TO_STREAM:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.DEBUG)
        stream_formatter = logging.Formatter('%(asctime)s - %(message)s')
        stream_handler.setFormatter(stream_formatter)
        logger.addHandler(stream_handler)

    if SEND_LOGS_TO_BOT:
        bot_handler = BotHandler()
        bot_handler.setLevel(logging.INFO)
        bot_formatter = logging.Formatter('%(message)s')
        bot_handler.setFormatter(bot_formatter)
        logger.addHandler(bot_handler)

    logger.debug('Bot started.')
    
    try:
        get_works()
    except KeyboardInterrupt:
        logger.debug('Program stopped.')
        exit()
    except Exception as e:
        logger.exception(e)
        raise e


if __name__ == '__main__':
    main()

