import logging
import os
import sys

from common.variables import ENCODING, LOGGING_LEVEL

LOGGER = logging.getLogger('client')

FORMAT = logging.Formatter('%(asctime)s %(levelname)-10s %(module)s %(message)s')

PATH = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(PATH, 'data/client.log')

STREAM_HANDLER = logging.StreamHandler(sys.stderr)
STREAM_HANDLER.setFormatter(FORMAT)
STREAM_HANDLER.setLevel(logging.ERROR)

FILE_HANDLER = logging.FileHandler(PATH, encoding=ENCODING)
FILE_HANDLER.setFormatter(FORMAT)

LOGGER.addHandler(FILE_HANDLER)
LOGGER.addHandler(STREAM_HANDLER)
LOGGER.setLevel(LOGGING_LEVEL)

if __name__ == '__main__':
    LOGGER.debug('Отладка')
    LOGGER.info('Информация')
    LOGGER.warning('Предупреждение')
    LOGGER.error('Ошибка')
    LOGGER.critical('Критическая ошибка')
