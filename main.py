"""
Telegram bot checking the lessons at DVMN site and reporting the result.
"""
import sys
import requests
import telegram
import logging
from logging.handlers import RotatingFileHandler
from textwrap import dedent
from time import sleep
from config import URL, HEADERS, TIMEOUT, TG_TOKEN, CHAT_ID, CONNECTION_RETRY_WAITING_TIME


logger = logging.getLogger(__file__)

is_negative_text = {
    True: 'К сожалению, в работе нашлись ошибки.',
    False: 'Задание выполнено, можете приступать к следующему уроку.'
}


def get_parsed_answer(attempts: list) -> str:
    answer = ''
    for attempt in attempts:
        answer += f"""
        Проверена работа {attempt['lesson_title']}
        {is_negative_text[attempt['is_negative']]}
        Ссылка на задачу: {attempt['lesson_url']}
        """

    return dedent(answer)


def send_tg_message(text: str, chat_id=CHAT_ID, token=TG_TOKEN):
    """Send message to TG chat with chat_id using TG token."""
    bot = telegram.Bot(token=token)
    bot.send_message(chat_id=chat_id, text=text)
    logger.info('Message sent.')


def get_works():
    """Get reviewed works at DVMN server."""
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
            logger.info('Timeout. No new works.')
            continue
        except requests.ConnectionError:
            logger.warning('No server connection.')
            for i in range(CONNECTION_RETRY_WAITING_TIME):
                sleep(1)            
            continue

        works = response.json()
        if works['status'] == 'timeout':
            request_params["timestamp"] = works["timestamp_to_request"]
            continue

        if works['status'] == 'found':
            logger.info('Found reviewed works.')
            request_params["timestamp"] = works["last_attempt_timestamp"]
            answer = get_parsed_answer(works['new_attempts'])
            send_tg_message(answer)


def main():
    """Application entry point."""

    logger.setLevel(logging.INFO)

    file_handler = RotatingFileHandler("main.log", maxBytes=100000, backupCount=2)
    file_handler.setLevel(logging.INFO)
    file_handler_formatter = logging.Formatter('%(asctime)s - line %(lineno)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_handler_formatter)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    stream_formatter = logging.Formatter('%(asctime)s - %(message)s')
    stream_handler.setFormatter(stream_formatter)

    
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    logger.debug('Main.py started.')
    logger.info('Program started.')

    get_works()
    logger.debug('Done!')


if __name__ == '__main__':

    try:
        main()
    except KeyboardInterrupt:
        exit()
