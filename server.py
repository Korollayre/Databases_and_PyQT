"""Программа-сервер"""
import configparser
import os
import select
import socket
import sys
import logging
import argparse

from PyQt5.QtCore import QTimer, QSortFilterProxyModel
from PyQt5.QtWidgets import QApplication, QMessageBox, QHeaderView

import logs.server_log_config

from common.variables import *
from common.utils import get_message, send_message
from decos import Log
from descriptors import PortVerifier, AddressVerifier
from metaclasses import ServerVerifier
from server_database import ServerDatabase
from threading import Thread, Lock
from server_gui import MainWindow, HistoryWindow, ConfigurationWindow, active_users_table_create, \
    users_history_table_create

SERVER_LOGGER = logging.getLogger('server')

new_connection = False
connection_flag_lock = Lock()


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

    def init_socket(self):
        SERVER_LOGGER.info(f'Сервер запущен. Порт для подключения: {self.listen_port}, адрес: {self.listen_address}. '
                           f'При отсутствии адреса сервер принимает соединения со любых адресов')

        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.bind((self.listen_address, self.listen_port))
        transport.settimeout(0.5)

        self.sock = transport
        self.sock.listen(MAX_CONNECTIONS)

        SERVER_LOGGER.info(f'Настройка сокета завершена.')

    def run(self):
        global new_connection
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
            except OSError as error:
                SERVER_LOGGER.error(f'Ошибка работы с сокетами - {error}')
            if recv_sockets_list:
                for sender in recv_sockets_list:
                    try:
                        self.process_user_message(get_message(sender), sender)
                    except Exception:
                        SERVER_LOGGER.info(f'Соединение с {sender.getpeername()} разорвано.')
                        for name in self.names:
                            if self.names[name] == sender:
                                self.database.user_logout(name)
                                del self.names[name]
                                break
                        self.clients_list.remove(sender)
                        with connection_flag_lock:
                            new_connection = True

            for message in self.messages_list:
                try:
                    self.process_message(message, send_sockets_list)
                except Exception:
                    SERVER_LOGGER.info(f'Соединение с клиентом {message[DESTINATION]} разорвана.')
                    self.clients_list.remove(self.names[message[DESTINATION]])
                    del self.names[message[DESTINATION]]
                    with connection_flag_lock:
                        new_connection = True
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
        global new_connection
        SERVER_LOGGER.info(f'Разбор сообщения {message}.')
        if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:

            if message[USER][ACCOUNT_NAME] not in self.names.keys():
                self.names[message[USER][ACCOUNT_NAME]] = user
                user_address, user_port = user.getpeername()
                self.database.user_login(message[USER][ACCOUNT_NAME], user_address, user_port)
                send_message(user, {RESPONSE: 200})
                with connection_flag_lock:
                    new_connection = True
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
                and SENDER in message and MESSAGE_TEXT in message and self.names[message[SENDER]] == user:
            if message[DESTINATION] in self.names:
                self.messages_list.append(message)
                self.database.message_exchange(message[SENDER], message[DESTINATION])
                send_message(user, {RESPONSE: 200})
                SERVER_LOGGER.info(f'Добавление сообщения {message} в очередь.')
            else:
                send_message(user, {
                    RESPONSE: 400,
                    ERROR: 'Пользователь не зарегистрирован на сервере.'
                })
            return

        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == user:
            self.database.user_logout(message[ACCOUNT_NAME])
            self.clients_list.remove(self.names[message[ACCOUNT_NAME]])
            self.names[message[ACCOUNT_NAME]].close()
            del self.names[message[ACCOUNT_NAME]]
            with connection_flag_lock:
                new_connection = True
            SERVER_LOGGER.info(f'Завершение соединения по запросу пользователя.')
            return

        elif ACTION in message and message[ACTION] == GET_CONTACTS and USER in message and \
                self.names[message[USER]] == user:
            response = {RESPONSE: 202, LIST_INFO: self.database.get_contacts(message[USER])}
            send_message(user, response)

        elif ACTION in message and message[ACTION] == ADD_CONTACT and ACCOUNT_NAME in message and USER in message \
                and self.names[message[USER]] == user:
            self.database.add_contact(message[USER], message[ACCOUNT_NAME])
            send_message(user, {RESPONSE: 200})

        elif ACTION in message and message[ACTION] == REMOVE_CONTACT and ACCOUNT_NAME in message and USER in message \
                and self.names[message[USER]] == user:
            self.database.remove_contact(message[USER], message[ACCOUNT_NAME])
            send_message(user, {RESPONSE: 200})

        elif ACTION in message and message[ACTION] == USERS_REQUEST and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == user:
            response = {RESPONSE: 202, LIST_INFO: [user[0] for user in self.database.active_users_list()]}
            send_message(user, response)

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
def arg_parser(default_port, default_address):
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=default_port, type=int, nargs='?')
    parser.add_argument('-a', default=default_address, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p

    return listen_address, listen_port


def admin_gui(settings, database):
    app = QApplication(sys.argv)
    main_window = MainWindow()

    main_window.statusBar().showMessage('Server Working')
    main_window.active_clients_table.setModel(active_users_table_create(database))

    active_users_table_headers = main_window.active_clients_table.horizontalHeader()
    active_users_table_headers.setSectionResizeMode(0, QHeaderView.Stretch)
    active_users_table_headers.setSectionResizeMode(1, QHeaderView.Stretch)
    active_users_table_headers.setSectionResizeMode(2, QHeaderView.Stretch)
    active_users_table_headers.setSectionResizeMode(3, QHeaderView.Stretch)

    def active_users_table_update():
        global new_connection
        if new_connection:
            main_window.active_clients_table.setModel(
                active_users_table_create(database))
            with connection_flag_lock:
                new_connection = False

    def show_history():
        global history_window
        history_window = HistoryWindow()

        model = users_history_table_create(database)
        filter_model = QSortFilterProxyModel()
        filter_model.setSourceModel(model)
        filter_model.setFilterKeyColumn(0)

        history_window.search_field.textChanged.connect(filter_model.setFilterRegExp)

        history_window.history_table.setModel(filter_model)

        history_table_headers = history_window.history_table.horizontalHeader()
        history_table_headers.setSectionResizeMode(0, QHeaderView.Stretch)
        history_table_headers.setSectionResizeMode(1, QHeaderView.Stretch)
        history_table_headers.setSectionResizeMode(2, QHeaderView.Stretch)
        history_table_headers.setSectionResizeMode(3, QHeaderView.Stretch)

        history_window.show()

    def server_settings():
        global settings_window
        settings_window = ConfigurationWindow()
        settings_window.db_path.insert(settings['SETTINGS']['Database_path'])
        settings_window.db_file.insert(settings['SETTINGS']['Database_file'])
        settings_window.port.insert(settings['SETTINGS']['Default_port'])
        settings_window.address.insert(settings['SETTINGS']['Listen_Address'])
        settings_window.save_btn.clicked.connect(save_server_settings)

    def save_server_settings():
        global settings_window
        message = QMessageBox()
        settings['SETTINGS']['Database_path'] = settings_window.db_path.text()
        settings['SETTINGS']['Database_file'] = settings_window.db_file.text()
        try:
            port = int(settings_window.port.text())
        except ValueError:
            message.warning(settings_window, 'Error', 'Порт должен быть числом')
        else:
            settings['SETTINGS']['Listen_address'] = settings_window.address.text()
            if 1023 < port < 65536:
                settings['SETTINGS']['Default_port'] = str(port)
                with open('server.ini', 'w') as conf:
                    settings.write(conf)
                    message.information(settings_window, 'Successful', 'Настройки успешно сохранены!')
            else:
                message.warning(settings_window, 'Error', 'Порт должен быть в диапазоне от 1024 до 65536')

    timer = QTimer()
    timer.timeout.connect(active_users_table_update)
    timer.start(1000)

    main_window.refresh_button.triggered.connect(active_users_table_update)
    main_window.history_view_button.triggered.connect(show_history)
    main_window.configuration_button.triggered.connect(server_settings)

    app.exec_()


def main():
    settings = configparser.ConfigParser()

    dir_path = os.path.dirname(os.path.realpath(__file__))
    settings.read(f"{dir_path}/{'server.ini'}")

    database = ServerDatabase(
        os.path.join(
            settings['SETTINGS']['Database_path'],
            settings['SETTINGS']['Database_file']))

    listen_address, listen_port = arg_parser(settings['SETTINGS']['Default_port'],
                                             settings['SETTINGS']['Listen_Address'])

    server = Server(listen_address, listen_port, database)

    admin_gui_thread = Thread(target=admin_gui, args=(settings, database))
    admin_gui_thread.daemon = True
    admin_gui_thread.start()

    server.run()


if __name__ == '__main__':
    main()
