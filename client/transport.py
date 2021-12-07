import json
import socket
import threading
import time

import logging
import logs.client_log_config

from PyQt5.QtCore import QObject, pyqtSignal

from common.utils import get_message, send_message
from common.variables import *
from errors import ReqFieldMissingError, ServerError

CLIENT_LOGGER = logging.getLogger('client')

sock_lock = threading.Lock()


class ClientTransport(threading.Thread, QObject):
    new_message_signal = pyqtSignal(str)
    connection_lost_signal = pyqtSignal()

    def __init__(self, port, address, database, username):
        threading.Thread.__init__(self)
        QObject.__init__(self)

        self.database = database
        self.username = username

        self.transport = None

        self.connection_init(port, address)

        try:
            self.users_list_request()
            self.contacts_list_request()
        except OSError as error:
            if error.errno:
                CLIENT_LOGGER.critical(f'Потеряно соединение с сервером.')
                raise ServerError('Потеряно соединение с сервером!')
            CLIENT_LOGGER.error('Timeout соединения при обновлении списков пользователей (контактов).')
        except json.JSONDecodeError:
            CLIENT_LOGGER.error('Не удалось декодировать сообщение сервера.')
            raise ServerError('Не удалось декодировать сообщение сервера.')
        self.running = True

    def user_request(self):
        user_data = {
            ACTION: PRESENCE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: self.user_name
            }
        }
        CLIENT_LOGGER.info(f'Генерация запроса {PRESENCE} пользователя {self.user_name}')
        return user_data

    def parsing_server_response(self, response):
        CLIENT_LOGGER.info(f'Принят ответ сервера')
        if RESPONSE in response:
            if response[RESPONSE] == 200:
                return
            elif response[RESPONSE] == 400:
                raise ServerError(f'400 : {response[ERROR]}')
            else:
                CLIENT_LOGGER.error(f'Принят неизвестный код подтверждения {response[RESPONSE]}')
                raise ReqFieldMissingError(RESPONSE)

        elif ACTION in response and response[ACTION] == MESSAGE and SENDER in response \
                and MESSAGE_TEXT in response and DESTINATION in response and \
                response[DESTINATION] == self.account_name:
            CLIENT_LOGGER.info(f'Получено сообщение {response[MESSAGE_TEXT]} от пользователя {response[SENDER]}')
            self.database.save_user_message(response[SENDER], self.account_name, response[MESSAGE_TEXT])
            self.new_message_signal.emit(response[SENDER])

    def connection_init(self, port, address):
        connected = False

        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.transport.settimeout(5)

        for times in range(5):
            CLIENT_LOGGER.info(f'Попытка подключения к серверу №{times}')
            try:
                self.transport.connect((address, port))
            except(OSError, ConnectionRefusedError):
                pass
            else:
                connected = True
                break
            time.sleep(1)

        if not connected:
            CLIENT_LOGGER.critical('Не удалось установить соединение с сервером.')
            raise ServerError('Не удалось установить соединение с сервером.')

        try:
            with sock_lock:
                send_message(self.transport, self.user_request())
                self.parsing_server_response(get_message(self.transport))
        except OSError:
            CLIENT_LOGGER.critical('Потеряно соединение с сервером!')
            raise ServerError('Потеряно соединение с сервером!')
        except json.JSONDecodeError:
            CLIENT_LOGGER.error('Не удалось декодировать сообщение сервера.')
            raise ServerError('Не удалось декодировать сообщение сервера.')

        CLIENT_LOGGER.info('Соединение с сервером установлено.')

    def users_list_request(self):
        CLIENT_LOGGER.info(f'Запрос активных пользователей пользователем {self.username}')
        request = {
            ACTION: USERS_REQUEST,
            TIME: time.time(),
            ACCOUNT_NAME: self.username,
        }
        with sock_lock:
            send_message(self.transport, request)
            server_answer = get_message(self.transport)
        if RESPONSE in server_answer and server_answer[RESPONSE] == 202:
            self.database.init_active_users(server_answer[LIST_INFO])
        else:
            CLIENT_LOGGER.error('Не удалось обновить список активных пользователей.')

    def contacts_list_request(self):
        CLIENT_LOGGER.info(f'Запрос списка контактов пользователем {self.username}')
        request = {
            ACTION: GET_CONTACTS,
            TIME: time.time(),
            USER: self.username,
        }
        with sock_lock:
            send_message(self.transport, request)
            server_answer = get_message(self.transport)
        if RESPONSE in server_answer and server_answer[RESPONSE] == 202:
            for contact in server_answer[LIST_INFO]:
                self.database.add_contact(contact)
        else:
            CLIENT_LOGGER.error(f'Не удалось обновить список контактов пользователя {self.username}.')

    def add_contact_to_server(self, contact):
        CLIENT_LOGGER.info(f'Запрос на добавление в контакты пользователя {contact} пользователем {self.username}')
        request = {
            ACTION: ADD_CONTACT,
            TIME: time.time(),
            USER: self.username,
            ACCOUNT_NAME: contact,
        }
        with sock_lock:
            send_message(self.transport, request)
            self.parsing_server_response(get_message(self.transport))

    def remove_contact_from_server(self, contact):
        CLIENT_LOGGER.info(
            f'Запрос на удаление пользователя {contact} из списка контактов пользователем {self.username}')
        request = {
            ACTION: REMOVE_CONTACT,
            TIME: time.time(),
            USER: self.username,
            ACCOUNT_NAME: contact,
        }
        with sock_lock:
            send_message(self.transport, request)
            self.parsing_server_response(get_message(self.transport))

    def creat_user_message(self, receiver, message):
        user_message = {
            ACTION: MESSAGE,
            SENDER: self.username,
            DESTINATION: receiver,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        CLIENT_LOGGER.info(f'Сформировано сообщение {user_message}.')

        with sock_lock:
            send_message(self.transport, user_message)
            self.parsing_server_response(get_message(self.transport))
            CLIENT_LOGGER.info(f'Сообщение {user_message} пользователю {receiver} отправлено.')

    def transport_shutdown(self):
        self.running = False
        message = {
            ACTION: EXIT,
            TIME: time.time(),
            DESTINATION: self.username
        }
        with sock_lock:
            try:
                send_message(self.transport, message)
            except OSError:
                pass
        CLIENT_LOGGER.info('Завершение работы по запросу пользователя.')
        time.sleep(0.5)

    def run(self):
        CLIENT_LOGGER.info('Запущен процесс-приёмник сообщений сервера.')
        while self.running:
            time.sleep(1)
            with sock_lock:
                try:
                    self.transport.settimeout(0.5)
                    response = get_message(self.transport)
                except OSError:
                    CLIENT_LOGGER.critical('Потеряно соединение с сервером.')
                    self.running = False
                    self.connection_lost_signal.emit()
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError, TypeError):
                    CLIENT_LOGGER.critical('Потеряно соединение с сервером.')
                    self.running = False
                    self.connection_lost_signal.emit()
                else:
                    CLIENT_LOGGER.info(f'Ответ сервера принят: {response}')
                    self.parsing_server_response(response)
                finally:
                    self.transport.settimeout(0.5)
