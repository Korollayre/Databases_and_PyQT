import inspect
import logging
import sys
import traceback
from socket import socket

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

def login_required(func):
    def checker(*args, **kwargs):
        from server.core import MessageProcessor
        from common.variables import ACTION, PRESENCE
        if isinstance(args[0], MessageProcessor):
            found = False
            for arg in args:
                if isinstance(arg, socket):
                    for client in args[0].names:
                        if args[0].names[client] == arg:
                            found = True
            for arg in args:
                if isinstance(arg, dict):
                    if ACTION in arg and arg[ACTION] == PRESENCE:
                        found = True
            if not found:
                raise TypeError
        return func(*args, **kwargs)

    return checker
