import logging
import os
import time

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


def send_message(bot, message):
    chat_id = TELEGRAM_CHAT_ID
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    bot.send_message(chat_id, text=message)


def get_api_answer(current_timestamp):
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != 200:
            message = 'API недоступен: status code is not 200'
            logging.error(message)
            raise Exception(message)
        return response.json()
    except Exception as error: 
        message = f'Ошибка обращения к API: {error}' 
        logging.error(message) 
        raise Exception(message)  
        
    
def check_response(response):
    """Проверка корректности ответа API."""
    if not isinstance(response, dict):
        logging.error('Ответ API не соответствует ожиданиям')
        raise TypeError('Ответ API не соответствует ожиданиям')
    if 'homeworks' not in response:
        logging.error('Отсутствует ключ homeworks')
        raise KeyError('Отсутствует ключ homeworks')
    if not isinstance(response['homeworks'], list):
        logging.errorr('Ответ API не соответствует ожиданиям')
        raise TypeError('Ответ API не соответствует ожиданиям')
    homework = response.get('homeworks')
    return homework 


def parse_status(homework):
    homework_name = homework['homework_name']
    homework_status = homework['status']
    verdict = HOMEWORK_STATUSES[homework_status]
    if homework_status in HOMEWORK_STATUSES:        
        verdict
    elif homework_status is None:
        logging.error('Отсутствует статус')
        raise Exception ('Отсутствует статус')
    elif homework_status is None:   
        logging.error('Отсутствует ключ homework_status')
        raise Exception('Отсутствует ключ homework_status')
    else:
        logging.error('Неожиданный статус')
        raise Exception('Неожиданный статус')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens(): 
    if PRACTICUM_TOKEN is None or \
            TELEGRAM_TOKEN is None or \
            TELEGRAM_CHAT_ID is None:
        return False
    return True

def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('Отсутствует обязательная переменная окружения')
        return False
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            logging.info('Список домашних работ получен')
            message = parse_status(homework)
            send_message (bot, message)
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message) 
            
            time.sleep(RETRY_TIME)
        else:
            send_message(bot, message)


if __name__ == '__main__':
    main()
