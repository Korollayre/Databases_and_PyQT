"""Константы"""

# Порт поумолчанию для сетевого ваимодействия
import logging

DEFAULT_PORT = 7777
# IP адрес по умолчанию для подключения клиента
DEFAULT_IP_ADDRESS = '127.0.0.1'
# Максимальная очередь подключений
MAX_CONNECTIONS = 5
# Максимальная длинна сообщения в байтах
MAX_PACKAGE_LENGTH = 1024
# Кодировка проекта
ENCODING = 'utf-8'
# Уровень логирования
LOGGING_LEVEL = logging.DEBUG

GET_CONTACTS = 'get_contacts'
LIST_INFO = 'data_list'
REMOVE_CONTACT = 'remove'
ADD_CONTACT = 'add'
USERS_REQUEST = 'get_users'

# Прококол JIM основные ключи:
ACTION = 'action'
TIME = 'time'
PORT = 'port'
USER = 'user'
ACCOUNT_NAME = 'account_name'
SENDER = 'sender'
MESSAGE = 'message'
MESSAGE_TEXT = 'mess_text'
EXIT = 'exit'
DESTINATION = 'destination'
DATA = 'bin'
PUBLIC_KEY_REQUEST = 'pubkey_need'
PUBLIC_KEY = 'pubkey'

# Прочие ключи, используемые в протоколе
PRESENCE = 'presence'
RESPONSE = 'response'
ERROR = 'error'
RESPONDEFAULT_IP_ADDRESSSE = 'respondefault_ip_addressse'