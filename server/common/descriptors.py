import logging
from ipaddress import ip_address

import logs.server_log_config

DESCRIPTORS_LOGGER = logging.getLogger('server')


class PortVerifier:
    """
    Класс-дескриптор для серверного значения порта.
    Позволяет использовать только порт в диапазоне от 1023 до 65536.
    При попытке использовать неподходящий номер порта генерирует исключение.
    """

    def __set__(self, instance, listen_port):
        if not 1023 < listen_port < 65536:
            DESCRIPTORS_LOGGER.critical(f'Попытка запуска сервера с указанием неподходящего порта {listen_port}.')
            raise ValueError('Попытка запуска сервера с указанием неподходящего порта.')
        instance.__dict__[self.name] = listen_port

    def __set_name__(self, owner, name):
        self.name = name


class AddressVerifier:
    """
    Класс-дескриптор для серверного значения адреса.
    Проверяет правильность ввода значения ip-адреса.
    При попытке использовать неподходящее значения ip-адреса генерирует исключение.
    """

    def __set__(self, instance, address):
        if address:
            try:
                listen_address = ip_address(address)
            except ValueError:
                DESCRIPTORS_LOGGER.critical('Введён неправильный ip-адрес.')
                raise ValueError('Введён неправильный ip-адрес.')
            instance.__dict__[self.name] = listen_address

    def __set_name__(self, owner, name):
        self.name = name
