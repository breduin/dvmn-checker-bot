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


def get_parsed_answer(attempts: list) -> str:
    is_negative_text = {
    True: 'К сожалению, в работе нашлись ошибки.',
    False: 'Задание выполнено, можете приступать к следующему уроку.'
}
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
            logger.info('Message sent.')


def main():
    """Application entry point."""
    class BotHandler(logging.Handler):

        def emit(self, record):
            log_entry = self.format(record)
            send_tg_message(log_entry)


    logger.setLevel(logging.DEBUG)

    file_handler = RotatingFileHandler("main.log", maxBytes=100000, backupCount=2)
    file_handler.setLevel(logging.INFO)
    file_handler_formatter = logging.Formatter('%(asctime)s - line %(lineno)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_handler_formatter)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    stream_formatter = logging.Formatter('%(asctime)s - %(message)s')
    stream_handler.setFormatter(stream_formatter)

    bot_handler = BotHandler()
    bot_handler.setLevel(logging.INFO)
    bot_formatter = logging.Formatter('%(message)s')
    bot_handler.setFormatter(bot_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.addHandler(bot_handler)

    logger.debug('Main.py started.')
    logger.info('Program started.')

    2/0
    get_works()

if __name__ == '__main__':

    try:
        main()
    except KeyboardInterrupt:
        logger.info('Program stopped.')
        exit()
    except ZeroDivisionError:
        logger.exception('Деление на ноль.')
        exit()
    

