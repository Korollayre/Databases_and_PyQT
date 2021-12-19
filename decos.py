import inspect
import logging
import sys
import traceback

import logs.client_log_config
import logs.server_log_config

if sys.argv[0].find('client') == -1:
    LOGGER = logging.getLogger('server')
else:
    LOGGER = logging.getLogger('client')


class Log:
    def __call__(self, func):
        def decorated(*args, **kwargs):
            splitter = '\\'
            res = func(*args, **kwargs)
            LOGGER.info(f'Произошел вызов функции {func.__name__} со следующими параметрами - {args}, {kwargs}. '
                        f'Вызов произошел из функции {traceback.format_stack()[0].split()[-1]} '
                        f'модуля {inspect.stack()[0][1].split(splitter)[-1]}')
            return res

        return decorated
