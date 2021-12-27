import argparse
import os
import sys

from Cryptodome.PublicKey import RSA
from PyQt5.QtWidgets import QApplication, QMessageBox

from client.client_database import ClientDatabase
from client.main_window import MainWindow
from client.transport import ClientTransport
from client.welcome_window import WelcomeWindow
from common.decos import Log
from common.errors import ServerError
from common.variables import *

CLIENT_LOGGER = logging.getLogger('client')


@Log()
def arg_parser():
    """
    Парсер аргументов командной строки. Возвращает кортеж из 4 элементов -
    адрес и порт сервера, имя пользователя, и пароль.
    Выполняет проверку корректности указанного значения порта.

    :return:
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    parser.add_argument('-p', '--password', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    request_address = namespace.addr
    request_port = namespace.port
    request_name = namespace.name
    request_password = namespace.password

    if not 1023 < request_port < 65536:
        CLIENT_LOGGER.critical(f'Указано неверное значение порта - {request_port}. В качестве порта может быть '
                               f'указано только число в диапазоне от 1024 до 65535.')
        sys.exit(1)

    return request_address, request_port, request_name, request_password


def main():
    """
    Основная функция клиентской части.
    Загружает и проверяет параметры командной строки.
    При отсутствии имени пользователя и(или) пароля запрашивает их у пользователя.
    Генерирует открытый ключ, осуществляет запуск клиентского GUI.

    :return:
    """
    request_address, request_port, request_name, request_password = arg_parser()

    app = QApplication(sys.argv)
    welcome_window = WelcomeWindow()

    if not request_name or not request_password:
        app.exec_()
        if welcome_window.enter_button_click:
            request_name = welcome_window.username_filed.text()
            request_password = welcome_window.user_password.text()
        else:
            sys.exit(0)

    if request_name and request_password:
        CLIENT_LOGGER.info(f'Запущен клиент со следующими параметрами: '
                           f'адрес - {request_address}, порт - {request_port}, имя - {request_name}')

        dir_path = os.path.dirname(os.path.realpath(__file__)) + '\\client'
        key_file = os.path.join(dir_path, f'{request_name}.key')
        if not os.path.exists(key_file):
            keys = RSA.generate(2048, os.urandom)
            with open(key_file, 'wb') as key:
                key.write(keys.export_key())
        else:
            with open(key_file, 'rb') as key:
                keys = RSA.import_key(key.read())

        CLIENT_LOGGER.info('Ключи успешно загружены.')

        database = ClientDatabase(request_name)

        try:
            client_transport = ClientTransport(request_port,
                                               request_address,
                                               database,
                                               request_name,
                                               request_password,
                                               keys)
        except ServerError as error:
            message = QMessageBox()
            message.critical(welcome_window, 'Ошибка сервера', error.text)
            CLIENT_LOGGER.critical(f'Сервер вернул ошибку - {error.text()}')
            sys.exit(1)

        del welcome_window

        client_transport.setDaemon(True)
        client_transport.start()

        main_window = MainWindow(database, client_transport, keys)
        main_window.make_connection(client_transport)
        app.exec_()

        client_transport.transport_shutdown()
        client_transport.join()


if __name__ == '__main__':
    main()
