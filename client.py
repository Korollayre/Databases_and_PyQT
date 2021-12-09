import argparse
import sys

from PyQt5.QtWidgets import QApplication

from client.client_database import ClientDatabase
from client.main_window import MainWindow
from client.transport import ClientTransport
from client.welcome_window import WelcomeWindow
from common.variables import *
from decos import Log
from errors import ServerError

CLIENT_LOGGER = logging.getLogger('client')

@Log()
def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    request_address = namespace.addr
    request_port = namespace.port
    request_name = namespace.name

    if not 1023 < request_port < 65536:
        CLIENT_LOGGER.critical(f'Указано неверное значение порта - {request_port}. В качестве порта может быть '
                               f'указано только число в диапазоне от 1024 до 65535.')
        sys.exit(1)

    return request_address, request_port, request_name


def main():
    request_address, request_port, request_name = arg_parser()

    app = QApplication(sys.argv)

    if not request_name:
        welcome_window = WelcomeWindow()
        app.exec_()

        if welcome_window.enter_button_click:
            request_name = welcome_window.username_filed.text()
            del welcome_window
        else:
            sys.exit(0)

    CLIENT_LOGGER.info(f'Запущен клиент со следующими параметрами: '
                       f'адрес - {request_address}, порт - {request_port}, имя - {request_name}')

    database = ClientDatabase(request_name)

    try:
        client_transport = ClientTransport(request_port, request_address, database, request_name)
    except ServerError as error:
        CLIENT_LOGGER.critical(f'Сервер вернул ошибку - {error.text()}')
        sys.exit(1)

    client_transport.setDaemon(True)
    client_transport.start()

    main_window = MainWindow(database, client_transport)
    main_window.make_connection(client_transport)
    app.exec_()

    client_transport.transport_shutdown()
    client_transport.join()


if __name__ == '__main__':
    main()
