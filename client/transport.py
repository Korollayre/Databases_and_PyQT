import binascii
import hashlib
import hmac
import json
import socket
import threading
import time

from PyQt5.QtCore import QObject, pyqtSignal

from common.errors import ReqFieldMissingError, ServerError
from common.utils import get_message, send_message
from common.variables import *

import logs.client_log_config

CLIENT_LOGGER = logging.getLogger('client')

sock_lock = threading.Lock()


class ClientTransport(threading.Thread, QObject):
    """
    Класс, отвечающий за взаимодействие с сервером.
    """
    new_message_signal = pyqtSignal(dict)
    message_205 = pyqtSignal()
    connection_lost_signal = pyqtSignal()

    def __init__(self, port, address, database, username, password, keys):
        threading.Thread.__init__(self)
        QObject.__init__(self)

        self.database = database
        self.username = username
        self.password = password
        self.keys = keys

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

    def parsing_server_response(self, response):
        """
        Метод, обрабатывающий сообщения сервера.

        :param response: сообщение сервера.
        :return:
        """
        CLIENT_LOGGER.info(f'Принят ответ сервера')
        if RESPONSE in response:
            if response[RESPONSE] == 200:
                return
            elif response[RESPONSE] == 400:
                raise ServerError(f'400 : {response[ERROR]}')
            elif response[RESPONSE] == 205:
                self.users_list_request()
                self.contacts_list_request()
                self.message_205.emit()
            else:
                CLIENT_LOGGER.error(f'Принят неизвестный код подтверждения {response[RESPONSE]}')
                raise ReqFieldMissingError(RESPONSE)

        elif ACTION in response and response[ACTION] == MESSAGE and SENDER in response \
                and MESSAGE_TEXT in response and DESTINATION in response and \
                response[DESTINATION] == self.username:
            CLIENT_LOGGER.info(f'Получено сообщение {response[MESSAGE_TEXT]} от пользователя {response[SENDER]}')
            self.new_message_signal.emit(response)

    def connection_init(self, port, address):
        """
        Метод, осуществляющий соединение с сервером и
        отправку запроса авторизации пользователя на сервере.

        :param port: порт подключения.
        :param address: адрес подключения.
        :return:
        """
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

        CLIENT_LOGGER.info('Запуск процесса авторизации.')

        password_bytes = self.password.encode('utf-8')
        salt = self.username.lower().encode('utf-8')
        password_hash = hashlib.pbkdf2_hmac('sha512', password_bytes, salt, 10000)
        password_hash_string = binascii.hexlify(password_hash)

        CLIENT_LOGGER.info(f'Создан хеш - {password_hash_string}')

        pubkey = self.keys.publickey().export_key().decode('ascii')

        with sock_lock:
            request = {
                ACTION: PRESENCE,
                TIME: time.time(),
                USER: {
                    ACCOUNT_NAME: self.username,
                    PUBLIC_KEY: pubkey
                }
            }
            CLIENT_LOGGER.info(f'Генерация запроса {PRESENCE} пользователя {self.username}')

            try:
                send_message(self.transport, request)
                server_answer = get_message(self.transport)
                if RESPONSE in server_answer:
                    if server_answer[RESPONSE] == 400:
                        raise ServerError(f'400: {server_answer[ERROR]}')
                    elif server_answer[RESPONSE] == 511:
                        data = server_answer[DATA]
                        current_hash = hmac.new(password_hash_string, data.encode('utf-8'), 'MD5')
                        digest = current_hash.digest()
                        send_message(self.transport, {RESPONSE: 511,
                                                      DATA: binascii.b2a_base64(digest).decode('ascii')})
                        self.parsing_server_response(get_message(self.transport))
            except OSError:
                CLIENT_LOGGER.critical('Потеряно соединение с сервером.')
                raise ServerError('Потеряно соединение с сервером.')
            except json.JSONDecodeError:
                CLIENT_LOGGER.error('Не удалось декодировать сообщение сервера.')
                raise ServerError('Не удалось декодировать сообщение сервера.')

        CLIENT_LOGGER.info('Соединение с сервером установлено.')

    def users_list_request(self):
        """
        Метод, обновляющий с сервера список пользователей онлайн.

        :return:
        """
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
        """
        Метод, обновляющий с сервера список контактов.

        :return:
        """
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

    def add_contact_to_server(self, user):
        """
        Метод, отправляющий на сервер сведения о добавления контакта.
        :param user: пользователь, добавленный в список контактов.
        :return:
        """
        CLIENT_LOGGER.info(f'Запрос на добавление в контакты пользователя {user} пользователем {self.username}')
        request = {
            ACTION: ADD_CONTACT,
            TIME: time.time(),
            USER: self.username,
            ACCOUNT_NAME: user,
        }
        with sock_lock:
            send_message(self.transport, request)
            self.parsing_server_response(get_message(self.transport))

    def remove_contact_from_server(self, contact):
        """
        Метод, отправляющий на сервер сведения об удалении пользователя из списка контактов.
        :param contact: пользователь, удаленный из списка контактов.
        :return:
        """
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

    def create_user_message(self, receiver, message):
        """
        Метод, отправляющий на сервер сообщение для определенного пользователя.

        :param receiver: получатель сообщения.
        :param message: сообщение.
        :return:
        """
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

    def user_key_request(self, username):
        """
        Метод, запрашивающий с сервера публичный ключ пользователя.

        :param username: пользователь, чей публичный ключ запрашивается.
        :return:
        """
        CLIENT_LOGGER.info(f'Запрос публичного ключа пользователя {username}')
        request = {
            ACTION: PUBLIC_KEY_REQUEST,
            TIME: time.time(),
            ACCOUNT_NAME: username,
        }
        with sock_lock:
            send_message(self.transport, request)
            server_answer = get_message(self.transport)
        if RESPONSE in server_answer and server_answer[RESPONSE] == 511:
            return server_answer[DATA]
        else:
            CLIENT_LOGGER.error(f'Не удалось получить публичный ключ пользователя {username}.')

    def transport_shutdown(self):
        """
        Метод, отправляющий серверу сведения о завершение работы клиентского приложения.
        :return:
        """
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
        """
        Метод, содержащий основной цикл работы класса.

        :return:
        """
        CLIENT_LOGGER.info('Запущен процесс-приёмник сообщений сервера.')
        while self.running:
            time.sleep(1)
            with sock_lock:
                try:
                    self.transport.settimeout(0.5)
                    response = get_message(self.transport)
                except OSError as error:
                    if error.errno:
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
                    self.transport.settimeout(5)
