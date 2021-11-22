import logging
import sys

DESCRIPTORS_LOGGER = logging.getLogger('server')


class PortVerifier:
    def __set__(self, instance, listen_port):
        if not 1023 < listen_port < 65536:
            DESCRIPTORS_LOGGER.critical(f'Попытка запуска сервера с указанием неподходящего порта {listen_port}')
            sys.exit(1)
        instance.__dict__[self.name] = listen_port

    def __set_name__(self, owner, name):
        self.name = name
