"""Программа-сервер"""
import select
import socket
import sys
import logging
import argparse
import logs.server_log_config

from common.variables import *
from common.utils import get_message, send_message
from decos import Log
from descriptors import PortVerifier, AddressVerifier
from metaclasses import ServerVerifier
from server_database import ServerDatabase
from threading import Thread

SERVER_LOGGER = logging.getLogger('server')


class Server(metaclass=ServerVerifier):
    port = PortVerifier()
    address = AddressVerifier()

    def __init__(self, listen_address, listen_port, database):
        self.listen_address = listen_address
        self.listen_port = listen_port

        self.database = database

        self.clients_list = []
        self.messages_list = []
        self.names = {}

    def help_messages(self):
        print("Поддерживаемые команды: \n"
              "'users' - список зарегистрированных пользователей.\n"
              "'connected' - список пользователей онлайн.\n"
              "'history' - история посещения пользователя.\n"
              "'users' - список зарегистрированных пользователей.\n"
              "'help' - вызов справки.\n"
              "'exit' - завершение работы программы.")

    def init_socket(self):
        SERVER_LOGGER.info(f'Сервер запущен. Порт для подключения: {self.listen_port}, адрес: {self.listen_address}. '
                           f'При отсутствии адреса сервер принимает соединения со любых адресов')
        # Готовим сокет
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.bind((self.listen_address, self.listen_port))
        transport.settimeout(1)

        # Слушаем порт
        self.sock = transport
        self.sock.listen(MAX_CONNECTIONS)

        SERVER_LOGGER.info(f'Настройка сокета завершена.')

    def run(self):
        # Инициализируем сокет
        self.init_socket()

        while True:
            try:
                user, user_address = self.sock.accept()
            except OSError:
                pass
            else:
                SERVER_LOGGER.info(f'Соединение с {user_address} установлено')
                self.clients_list.append(user)

            recv_sockets_list, send_sockets_list, errors_sockets_list = [], [], []

            try:
                if self.clients_list:
                    recv_sockets_list, send_sockets_list, errors_sockets_list = select.select(self.clients_list,
                                                                                              self.clients_list,
                                                                                              [], 0)
            except OSError:
                pass
            if recv_sockets_list:
                for sender in recv_sockets_list:
                    try:
                        self.process_user_message(get_message(sender), sender)
                    except Exception:
                        SERVER_LOGGER.info(f'Соединение с {sender.getpeername()} разорвано.')
                        sender.close()
                        self.clients_list.remove(sender)

            for message in self.messages_list:
                try:
                    self.process_message(message, send_sockets_list)
                except Exception:
                    SERVER_LOGGER.info(f'Соединение с клиентом {message[DESTINATION]} разорвана.')
                    self.clients_list.remove(self.names[message[DESTINATION]])
                    del self.names[message[DESTINATION]]
            self.messages_list.clear()

    def process_user_message(self, message, user):
        """
        Обработчик сообщений от клиентов, принимает словарь -
        сообщение от клинта, проверяет корректность,
        возвращает словарь-ответ для клиента

        :param message:
        :param user:
        :return:
        """
        SERVER_LOGGER.info(f'Разбор сообщения {message}.')
        if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
            if message[USER][ACCOUNT_NAME] not in self.names.keys():
                self.names[message[USER][ACCOUNT_NAME]] = user
                user_address, user_port = user.getpeername()
                self.database.user_login(message[USER][ACCOUNT_NAME], user_address, user_port)
                send_message(user, {RESPONSE: 200})
                SERVER_LOGGER.info(f'Зарегистрирован новый пользователь {user}.')
            else:
                send_message(user, {
                    RESPONSE: 400,
                    ERROR: 'Имя пользователя уже занято.'
                })
                SERVER_LOGGER.info(f'Попытка создания пользователя с существующим именем. Закрытие соединения.')
                self.clients_list.remove(user)
                user.close()
            return
        elif ACTION in message and message[ACTION] == MESSAGE and DESTINATION in message and TIME in message \
                and SENDER in message and MESSAGE_TEXT in message:
            self.messages_list.append(message)
            SERVER_LOGGER.info(f'Добавление сообщения {message} в очередь.')
            return
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
            self.database.user_logout(message[ACCOUNT_NAME])
            self.clients_list.remove(self.names[message[ACCOUNT_NAME]])
            self.names[message[ACCOUNT_NAME]].close()
            del self.names[message[ACCOUNT_NAME]]
            SERVER_LOGGER.info(f'Завершение соединения по запросу пользователя.')
            return
        else:
            send_message(user, {
                RESPONSE: 400,
                ERROR: 'Bad Request'})
            return

    def process_message(self, message, listen_address):
        """
        Функция адресной отправки сообщения определённому клиенту. Принимает словарь сообщение,
        список зарегистрированных пользователей и слушающие сокеты. Ничего не возвращает.
        :param listen_address:
        :param message:
        :return:
        """
        if message[DESTINATION] in self.names and self.names[message[DESTINATION]] in listen_address:
            send_message(self.names[message[DESTINATION]], message)
            SERVER_LOGGER.info(
                f'Отправлено сообщение {message} пользователю {message[DESTINATION]} пользователем {message[SENDER]}.')
        elif message[DESTINATION] in self.names and self.names[message[DESTINATION]] not in listen_address:
            raise ConnectionError
        else:
            SERVER_LOGGER.error(
                f'Пользователь {message[DESTINATION]} не зарегистрирован. Отправка сообщения невозможна.')


@Log()
def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p

    return listen_address, listen_port


def poll(cls, database):
    cls.help_messages()
    while True:
        command = input('\nВведите команду: ')
        if command == 'help':
            cls.help_messages()
        elif command == 'exit':
            break
        elif command == 'users':
            for user in sorted(database.users_list()):
                print(f'Пользователь - {user[0]}, последний вход - {user[1]}.')
        elif command == 'connected':
            for user in sorted(database.active_users_list()):
                print(f'Пользователь - {user[0]}, ip - {user[1]}, port - {user[2]}, время подключения - {user[3]}.')
        elif command == 'history':
            username = input('Введите имя пользователя для просмотра его истории посещения. '
                             'Для вывода всей истории, просто нажмите Enter: ')
            for user in sorted(database.login_history(username)):
                print(f'Пользователь - {user[0]}, время входа - {user[1]}, ip - {user[2]}, port - {user[3]}.')
        else:
            print("Не удалось распознать команду. Попробуйте снова (для вызова справки введите 'help').")


def main():
    database = ServerDatabase()
    listen_address, listen_port = arg_parser()

    server = Server(listen_address, listen_port, database)

    poll_thread = Thread(target=poll, args=(server, database))
    poll_thread.daemon = True
    poll_thread.start()

    server.run()


if __name__ == '__main__':
    main()
