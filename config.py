from os import environ
from dotenv import load_dotenv

env_file = '.env'

load_dotenv(env_file)

BOT_TOKEN = environ.get('BOT_TOKEN')
BOT_URL = environ.get('BOT_URL')

ADMIN_IDS = ['1460183114']

TELEGRAM_WEBHOOK_PATH = '/telegram_webhook/'
WEBHOOK_URL = 'https://9b93-82-7-67-196.ngrok-free.app'
WEBHOOK_PORT = 8080
API_VERSION = 'v1'
API_PATH = f'/api/{API_VERSION}'

SERVER_IP = environ.get('SERVER_IP')
SUPER_ADMIN_ID = environ.get('SUPER_ADMIN_ID')
TS_USERNAME = environ.get('TS_USERNAME')
SENIOR_MENTOR_USERNAME = environ.get('SENIOR_MENTOR_USERNAME')
TIMEZONE = environ.get('TIMEZONE')


class Database:
    USER = environ.get('DB_USER')
    PASSWORD = environ.get('DB_PASSWORD')
    NAME = environ.get('DB_NAME')
    HOST = environ.get('DB_HOST')
    PORT = environ.get('DB_PORT')
    DIALECT = environ.get('DB_DIALECT')
    DATABASE_URL = f"{DIALECT}://{USER}:{PASSWORD}@{HOST}:{PORT}/{NAME}"


class Chat:
    CHAT_DRAWING_LOGS = environ.get('CHAT_DRAWING_LOGS')
