import logging
import os
import time
from json.decoder import JSONDecodeError

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)


class HomeworkbotException(Exception):
    pass

def send_message(bot, message):
    """Функция отправки сообщения."""
    chat_id = TELEGRAM_CHAT_ID
    try:
        bot.send_message(chat_id, text=message)
        logging.info('Сообщение отправлено.')
    except Exception as error:
        message = f'Ошибка отправки сообщения: {error}'
        logging.error(message)
        raise HomeworkbotException(message)


def get_api_answer(current_timestamp):
    """Проверка доступности API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    logging.info("Получение ответа от сервера")
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != 200:
            message = 'API недоступен: status code is not 200'
            raise HomeworkbotException(message)
    except ConnectionError as error:
        message = f'Ошибка обращения к API: {error}'
        logging.error(message)
        raise HomeworkbotException(message)
    try:
        return response.json()
    except JSONDecodeError:
        raise HomeworkbotException(
            'Ответ должен быть в формате JSON'
        )


def check_response(response):
    """Проверка корректности ответа API."""
    if not isinstance(response, dict):
        logging.error('Ответ API не соответствует ожиданиям')
        raise TypeError('Ответ API не соответствует ожиданиям')
    if 'homeworks' not in response:
        logging.error('Отсутствует ключ homeworks')
        raise KeyError('Отсутствует ключ homeworks')
    if not isinstance(response['homeworks'], list):
        logging.error('Ответ API не соответствует ожиданиям')
        raise TypeError('Ответ API не соответствует ожиданиям')
    homework = response.get('homeworks')
    return homework


def parse_status(homework):
    """Проверка информации о конкретной домашней работе."""
    logging.debug(f"Получаем домашнее задание: {homework}")
    homework_name = homework['homework_name']
    homework_status = homework['status']
    verdict = HOMEWORK_STATUSES[homework_status]
    logging.info('Список домашних работ получен')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка наличия токенов."""
    if (PRACTICUM_TOKEN  is None or
            TELEGRAM_TOKEN is None or
            TELEGRAM_CHAT_ID is None):
        return False
    return True


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('Отсутствует обязательная переменная окружения')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    logging.info('Бот запущен!')
    response = get_api_answer(current_timestamp)
    while True:
        try:
            homework = check_response(response)
            message = parse_status(homework[0])
            logging.info('Отсутствуют новые статусы')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            old_message = ''
            if message != old_message:
                send_message(bot, message) 
                logging.info('Сообщение с ошибкой отправлено.')
            old_message = message
        else:
            send_message(bot, message)
        finally:
            time.sleep(RETRY_TIME)
    
if __name__ == '__main__':
    main()
