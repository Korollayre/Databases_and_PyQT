"""
Файл конфигурации серверного логгера.
"""

import logging
import os
import sys
from logging import handlers

from common.variables import ENCODING, LOGGING_LEVEL

LOGGER = logging.getLogger('server')

FORMAT = logging.Formatter('%(asctime)s %(levelname)-10s %(module)s %(message)s')

PATH = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(PATH, 'data/server.log')

STREAM_HANDLER = logging.StreamHandler(sys.stderr)
STREAM_HANDLER.setFormatter(FORMAT)
STREAM_HANDLER.setLevel(logging.ERROR)

ROTATING_FILE_HANDLER = logging.handlers.TimedRotatingFileHandler(PATH, when='D', interval=1, encoding=ENCODING)
ROTATING_FILE_HANDLER.setFormatter(FORMAT)

LOGGER.addHandler(ROTATING_FILE_HANDLER)
LOGGER.addHandler(STREAM_HANDLER)
LOGGER.setLevel(LOGGING_LEVEL)

if __name__ == '__main__':
    LOGGER.debug('Отладка')
    LOGGER.info('Информация')
    LOGGER.warning('Предупреждение')
    LOGGER.error('Ошибка')
    LOGGER.critical('Критическая ошибка')
