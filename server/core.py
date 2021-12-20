import argparse
import binascii
import configparser
import hmac
import os
import select
import socket
import sys
from json import JSONDecodeError
from threading import Lock, Thread

from PyQt5.QtCore import QSortFilterProxyModel, QTimer
from PyQt5.QtWidgets import QApplication, QHeaderView, QMessageBox

from common.utils import get_message, send_message
from common.variables import *
from common.decos import Log, login_required
from common.descriptors import AddressVerifier, PortVerifier
from common.metaclasses import ServerVerifier
from server.server_database import ServerDatabase
from server.main_window import (ConfigurationWindow, HistoryWindow, MainWindow,)

SERVER_LOGGER = logging.getLogger('server')


class MessageProcessor(Thread, metaclass=ServerVerifier):
    port = PortVerifier()
    address = AddressVerifier()

    def __init__(self, listen_address, listen_port, database):
        super(MessageProcessor, self).__init__()

        self.listen_address = listen_address
        self.listen_port = listen_port

        self.database = database

        self.clients_list = []

        self.names = {}

        self.running = True

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
        self.init_socket()

        while self.running:
            try:
                user, user_address = self.sock.accept()
            except OSError:
                pass
            else:
                SERVER_LOGGER.info(f'Соединение с {user_address} установлено')
                user.settimeout(5)
                self.clients_list.append(user)

            self.recv_sockets_list, self.send_sockets_list, self.errors_sockets_list = [], [], []

            try:
                if self.clients_list:
                    self.recv_sockets_list, self.send_sockets_list, self.errors_sockets_list = select.select(
                        self.clients_list,
                        self.clients_list,
                        [], 0)
            except OSError as error:
                SERVER_LOGGER.error(f'Ошибка работы с сокетами - {error}')
            if self.recv_sockets_list:
                for sender in self.recv_sockets_list:
                    try:
                        self.process_user_message(get_message(sender), sender)
                    except (OSError, JSONDecodeError, TypeError):
                        self.remove_user(sender)

    def remove_user(self, username):
        SERVER_LOGGER.info(f'Соединение с {username.getpeername()} разорвано.')
        for name in self.names:
            if self.names[name] == username:
                self.database.user_logout(name)
                del self.names[name]
                break
        self.clients_list.remove(username)
        username.close()

    @login_required
    def process_user_message(self, message, user):
        SERVER_LOGGER.info(f'Разбор сообщения {message}.')
        if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
            self.user_authorization(message, user)

        elif ACTION in message and message[ACTION] == MESSAGE and DESTINATION in message and TIME in message \
                and SENDER in message and MESSAGE_TEXT in message and self.names[message[SENDER]] == user:
            if message[DESTINATION] in self.names:
                self.database.message_exchange(message[SENDER], message[DESTINATION])
                self.process_message(message)
                try:
                    send_message(user, {RESPONSE: 200})
                    SERVER_LOGGER.info(f'Добавление сообщения {message} в очередь.')
                except OSError:
                    self.remove_user(user)
            else:
                try:
                    send_message(user, {
                        RESPONSE: 400,
                        ERROR: 'Пользователь не зарегистрирован на сервере.'
                    })
                except OSError:
                    pass
            return

        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == user:
            self.remove_user(user)

        elif ACTION in message and message[ACTION] == GET_CONTACTS and USER in message and \
                self.names[message[USER]] == user:
            response = {RESPONSE: 202, LIST_INFO: self.database.get_contacts(message[USER])}
            try:
                send_message(user, response)
            except OSError:
                self.remove_user(user)

        elif ACTION in message and message[ACTION] == ADD_CONTACT and ACCOUNT_NAME in message and USER in message \
                and self.names[message[USER]] == user:
            self.database.add_contact(message[USER], message[ACCOUNT_NAME])
            try:
                send_message(user, {RESPONSE: 200})
            except OSError:
                self.remove_user(user)

        elif ACTION in message and message[ACTION] == REMOVE_CONTACT and ACCOUNT_NAME in message and USER in message \
                and self.names[message[USER]] == user:
            self.database.remove_contact(message[USER], message[ACCOUNT_NAME])
            try:
                send_message(user, {RESPONSE: 200})
            except OSError:
                self.remove_user(user)

        elif ACTION in message and message[ACTION] == USERS_REQUEST and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == user:
            response = {RESPONSE: 202, LIST_INFO: [user[0] for user in self.database.active_users_list()]}
            try:
                send_message(user, response)
            except OSError:
                self.remove_user(user)

        elif ACTION in message and message[ACTION] == PUBLIC_KEY_REQUEST and ACCOUNT_NAME in message:
            response = {RESPONSE: 511, DATA: self.database.get_pubkey(message[ACCOUNT_NAME])}

            if response[DATA]:
                try:
                    send_message(user, response)
                except OSError:
                    self.remove_user(user)
            else:
                try:
                    send_message(user, {RESPONSE: 400, ERROR: 'Публичный ключ отсутствует.'})
                except OSError:
                    self.remove_user(user)

        else:
            try:
                send_message(user, {
                    RESPONSE: 400,
                    ERROR: 'Bad Request'})
            except OSError:
                self.remove_user(user)
            return

    def process_message(self, message):
        if message[DESTINATION] in self.names and self.names[message[DESTINATION]] in self.send_sockets_list:
            try:
                send_message(self.names[message[DESTINATION]], message)
                SERVER_LOGGER.info(
                    f'Отправлено сообщение {message} пользователю {message[DESTINATION]} пользователем {message[SENDER]}.')
            except OSError:
                self.remove_user(message[DESTINATION])

        elif message[DESTINATION] in self.names and self.names[message[DESTINATION]] not in self.send_sockets_list:
            SERVER_LOGGER.error(
                f'Пользователь {message[DESTINATION]} не найден. Отправка сообщения невозможна.')
            self.remove_user(self.names[message[DESTINATION]])
        else:
            SERVER_LOGGER.error(
                f'Пользователь {message[DESTINATION]} не зарегистрирован. Отправка сообщения невозможна.')

    def user_authorization(self, message, user_sock):
        if message[USER][ACCOUNT_NAME] in self.names.keys():
            try:
                SERVER_LOGGER.info('Попытка авторизации авторизованного клиента. Закрытие соединения.')
                send_message(user_sock, {
                    RESPONSE: 400,
                    ERROR: 'Имя пользователя уже занято.'
                })
            except OSError:
                pass
            self.clients_list.remove(user_sock)
            user_sock.close()
        elif not self.database.check_user(message[USER][ACCOUNT_NAME]):
            try:
                SERVER_LOGGER.info('Попытка авторизации незарегистрированного пользователя. Закрытие соединения.')
                send_message(user_sock, {
                    RESPONSE: 400,
                    ERROR: 'Пользователя с таким именем не существует.'
                })
            except OSError:
                pass
            self.clients_list.remove(user_sock)
            user_sock.close()
        else:
            SERVER_LOGGER.info(f'Авторизация пользователя {message[USER][ACCOUNT_NAME]}. Проверка пароля')
            b_str = binascii.hexlify(os.urandom(64))
            message_data = b_str.decode('ascii')
            current_hash = hmac.new(self.database.get_hash(message[USER][ACCOUNT_NAME]), b_str, 'MD5')
            digest = current_hash.digest()

            try:
                send_message(user_sock, {RESPONSE: 511, DATA: message_data})
                answer = get_message(user_sock)
            except OSError as error:
                SERVER_LOGGER.info(f'Ошибка авторизации - {error}')
                user_sock.close()
                return
            user_digest = binascii.a2b_base64(answer[DATA])

            if RESPONSE in answer and answer[RESPONSE] == 511 and hmac.compare_digest(digest, user_digest):
                self.names[message[USER][ACCOUNT_NAME]] = user_sock
                user_address, user_port = user_sock.getpeername()
                try:
                    send_message(user_sock, {RESPONSE: 200})
                except OSError:
                    self.remove_user(message[USER][ACCOUNT_NAME])

                self.database.user_login(
                    message[USER][ACCOUNT_NAME],
                    user_address,
                    user_port,
                    message[USER][PUBLIC_KEY])
            else:
                try:
                    send_message(user_sock, {RESPONSE: 400, ERROR: 'Неверный пароль.'})
                except OSError:
                    pass
                self.clients_list.remove(user_sock)
                user_sock.close()

    def service_update_lists(self):
        for user in self.names:
            try:
                send_message(self.names[user], {RESPONSE: 205})
            except OSError:
                self.remove_user(self.names[user])
