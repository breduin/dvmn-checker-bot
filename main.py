"""
Telegram bot checking the lessons at DVMN site and reporting the result.
"""
import requests
import telegram
from textwrap import dedent
from time import sleep
from tqdm import trange
from config import URL, HEADERS, TIMEOUT, TG_TOKEN, CHAT_ID, CONNECTION_RETRY_WAITING_TIME


is_negative_text = {
    True: 'К сожалению, в работе нашлись ошибки.',
    False: 'Задание выполнено, можете приступать к следующему уроку.'
}


def get_parsed_answer(attempts: list) -> str:
    answer = ''
    for attempt in attempts:
        answer += f"""\
        Проверена работа {attempt['lesson_title']}
        {is_negative_text[attempt['is_negative']]}
        Ссылка на задачу: {attempt['lesson_url']}
        """

    return dedent(answer)


def get_works():

    request_params = {}
    bot = telegram.Bot(token=TG_TOKEN)

    while True:
        print('Sending request ...')
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
            print('No server connection.')
            print(f'Waiting for {CONNECTION_RETRY_WAITING_TIME} seconds.')
            for i in trange(CONNECTION_RETRY_WAITING_TIME):
                sleep(1)            
            continue

        works = response.json()
        if works['status'] == 'timeout':
            request_params["timestamp"] = works["timestamp_to_request"]
            print('no new works.')
            continue

        if works['status'] == 'found':
            request_params["timestamp"] = works["last_attempt_timestamp"]
            answer = get_parsed_answer(works['new_attempts'])
            bot.send_message(chat_id=CHAT_ID, text=answer)


if __name__ == '__main__':

    try:
        get_works()
    except KeyboardInterrupt:
        exit()
