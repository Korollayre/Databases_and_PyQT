"""Программа-клиент"""

import sys
import json
import socket
import threading
import time
import logging
import argparse

from common.variables import *
from common.utils import get_message, send_message
from errors import ReqFieldMissingError, ServerError, IncorrectDataRecivedError
from decos import Log
from metaclasses import ClientVerifier
from client_database import ClientDatabase

CLIENT_LOGGER = logging.getLogger('client')

sock_lock = threading.Lock()
database_lock = threading.Lock()


class ClientSender(threading.Thread, metaclass=ClientVerifier):

    def __init__(self, sock, account_name, database):
        self.sock = sock
        self.account_name = account_name
        self.database = database
        super().__init__()

    def create_exit_message(self):
        return {
            ACTION: EXIT,
            TIME: time.time(),
            DESTINATION: self.account_name
        }

    def help_messages(self):
        print("\nПоддерживаемые команды: \n"
              "'message' - отправить сообщение.\n"
              "'help' - вызов справки.\n"
              "'edit' - редактирование списка контактов.\n"
              "'history' - история сообщений.\n"
              "'contacts' - вызов списка контактов.\n"
              "'exit' - завершение работы программы.")

    def edit_user_contacts(self):
        while True:
            request = input("\nДля добавления контакта введите 'add', для удаления - 'del'.\n"
                            "Для выхода из режима редактирования контактов введите 'exit': ").strip()
            if request == 'add':
                user = input('Введите имя пользователя: ').strip()
                with database_lock:
                    if not self.database.check_user_in_active(user):
                        print(f'Пользователь с именем {user} не найден.')
                        CLIENT_LOGGER.error('Попытка добавления несуществующего пользователя.')
                    else:
                        self.database.add_contact(user)
                        print(f'Пользователь {user} успешно добавлен.')
                        with sock_lock:
                            try:
                                add_contact_to_server(self.sock, self.account_name, user)
                            except ServerError as error:
                                CLIENT_LOGGER.error(f'При установке соединения сервер вернул ошибку: {error.text}')
            elif request == 'del':
                contact = input('Введите имя контакта: ').strip()
                with database_lock:
                    if not self.database.chek_user_contact(contact):
                        print(f'Контакт с именем {contact} не найден.')
                        CLIENT_LOGGER.error('Попытка удаления несуществующего контакта.')
                    else:
                        self.database.delete_contact(contact)
                        print(f'Пользователь {contact} успешно удален из контактов.')
                        with sock_lock:
                            try:
                                remove_contact_from_server(self.sock, self.account_name, contact)
                            except ServerError as error:
                                CLIENT_LOGGER.error(f'При установке соединения сервер вернул ошибку: {error.text}')
            elif request == 'exit':
                break
            else:
                print('Не удалось распознать команду. Попробуйте снова.\n')

    def show_user_history(self):
        while True:
            request = input("\nДля вывода входящих сообщений введите 'in', исходящих - 'out'.\n"
                            "Для выхода из режима просмотра сообщений введите 'exit'.\n"
                            "Для вывода всех сообщений нажмите 'Enter': ").strip()
            with database_lock:
                if request == 'in':
                    messages_list = self.database.get_user_messages_history(receiver=self.account_name)
                    for message in messages_list:
                        print(f'\nСообщение пользователя {message[0]} от {message[3]}:\n{message[2]}')
                elif request == 'out':
                    messages_list = self.database.get_user_messages_history(sender=self.account_name)
                    for message in messages_list:
                        print(f'\nСообщение пользователю {message[1]} от {message[3]}:\n{message[2]}')
                elif request == '':
                    messages_list = self.database.get_user_messages_history()
                    for message in messages_list:
                        print(f'\nСообщение пользователя {message[0]} пользователю {message[1]}'
                              f' от {message[3]}:\n{message[2]}')
                elif request == 'exit':
                    break
                else:
                    print('Не удалось распознать команду. Попробуйте снова.\n')

    def creat_user_message(self):
        receiver = input('Введите имя получателя: ').strip()
        message = input('Введите сообщение: ')

        with database_lock:
            if not self.database.check_user_in_active(receiver):
                CLIENT_LOGGER.error(
                    f'Попытка отправки сообщения несуществующему (неактивному) пользователю - {receiver}')
                return

        user_message = {
            ACTION: MESSAGE,
            SENDER: self.account_name,
            DESTINATION: receiver,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        CLIENT_LOGGER.info(f'Сформировано сообщение {user_message}.')

        with database_lock:
            self.database.save_user_message(self.account_name, receiver, message)

        with sock_lock:
            try:
                send_message(self.sock, user_message)
                print('Сообщение отправлено!')
                CLIENT_LOGGER.info(f'Сообщение {user_message} пользователю {receiver} отправлено.')
            except Exception:
                CLIENT_LOGGER.critical(f'Потеряно соединение с сервером.')
                sys.exit(1)

    def run(self):
        self.help_messages()
        while True:
            request = input('\nВведите команду: ').strip()
            if request == 'message':
                self.creat_user_message()
            elif request == 'help':
                self.help_messages()
            elif request == 'edit':
                self.edit_user_contacts()
            elif request == 'history':
                self.show_user_history()
            elif request == 'contacts':
                with database_lock:
                    contacts_list = self.database.get_user_contacts()
                print('\nВаш список контактов:\n')
                for contact in contacts_list:
                    print(contact)
            elif request == 'exit':
                with sock_lock:
                    try:
                        send_message(self.sock, self.create_exit_message())
                    except Exception:
                        pass
                    print('Закрытие соединения.')
                    CLIENT_LOGGER.info('Закрытие соединения по запросу пользователя.')
                time.sleep(0.5)
                break
            else:
                print("Не удалось распознать команду. Попробуйте снова (для вызова справки введите 'help').")


class ClientReader(threading.Thread, metaclass=ClientVerifier):

    def __init__(self, sock, account_name, database):
        self.sock = sock
        self.account_name = account_name
        self.database = database
        super().__init__()

    def run(self):
        while True:
            time.sleep(1)
            with sock_lock:
                try:
                    message = get_message(self.sock)
                except IncorrectDataRecivedError:
                    CLIENT_LOGGER.error(f'Не удалось декодировать полученное сообщение.')
                except (ConnectionError, ConnectionAbortedError,
                        ConnectionResetError, json.JSONDecodeError):
                    CLIENT_LOGGER.critical(f'Потеряно соединение с сервером.')
                    sys.exit(1)
                except OSError as err:
                    if err.errno:
                        CLIENT_LOGGER.critical(f'Потеряно соединение с сервером.')
                        sys.exit(1)
                else:
                    if ACTION in message and message[ACTION] == MESSAGE and SENDER in message \
                            and MESSAGE_TEXT in message and DESTINATION in message \
                            and message[DESTINATION] == self.account_name:
                        print(f'\nПолучено сообщение: {message[MESSAGE_TEXT]}.\nОт пользователя {message[SENDER]}\n'
                              f'Введите команду: ')
                        CLIENT_LOGGER.info(
                            f'Получено сообщение {message[MESSAGE_TEXT]} от пользователя {message[SENDER]}')
                        with database_lock:
                            try:
                                self.database.save_user_message(message[SENDER], self.account_name,
                                                                message[MESSAGE_TEXT])
                            except Exception:
                                CLIENT_LOGGER.error('Ошибка взаимодействия с базой данных.')
                    else:
                        CLIENT_LOGGER.error(f'Получено некорректное сообщение: {message}')


@Log()
def user_request(user_name):
    user_data = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: user_name
        }
    }
    CLIENT_LOGGER.info(f'Генерация запроса {PRESENCE} пользователя {user_name}')
    return user_data


@Log()
def server_response(response):
    CLIENT_LOGGER.info(f'Принят ответ сервера')
    if RESPONSE in response:
        if response[RESPONSE] == 200:
            return '200 : OK'
        elif response[RESPONSE] == 400:
            raise ServerError(f'400 : {response[ERROR]}')
    raise ReqFieldMissingError(RESPONSE)


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


def users_list_request(sock, username):
    CLIENT_LOGGER.info(f'Запрос активных пользователей пользователем {username}')
    request = {
        ACTION: USERS_REQUEST,
        TIME: time.time(),
        ACCOUNT_NAME: username,
    }
    send_message(sock, request)
    server_answer = get_message(sock)
    if RESPONSE in server_answer and server_answer[RESPONSE] == 202:
        return server_answer[LIST_INFO]
    else:
        raise ServerError('Ошибка запроса списка активных пользователей')


def contacts_list_request(sock, username):
    CLIENT_LOGGER.info(f'Запрос списка контактов пользователем {username}')
    request = {
        ACTION: GET_CONTACTS,
        TIME: time.time(),
        USER: username,
    }
    send_message(sock, request)
    server_answer = get_message(sock)
    if RESPONSE in server_answer and server_answer[RESPONSE] == 202:
        return server_answer[LIST_INFO]
    else:
        raise ServerError('Ошибка запроса списка контактов')


def add_contact_to_server(sock, username, contact):
    CLIENT_LOGGER.info(f'Запрос на добавление в контакты пользователя {contact} пользователем {username}')
    request = {
        ACTION: ADD_CONTACT,
        TIME: time.time(),
        USER: username,
        ACCOUNT_NAME: contact,
    }
    send_message(sock, request)
    server_answer = get_message(sock)
    if RESPONSE in server_answer and server_answer[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Ошибка добавления пользователя в список контактов')


def remove_contact_from_server(sock, username, contact):
    CLIENT_LOGGER.info(f'Запрос на удаление пользователя {contact} из списка контактов пользователем {username}')
    request = {
        ACTION: REMOVE_CONTACT,
        TIME: time.time(),
        USER: username,
        ACCOUNT_NAME: contact,
    }
    send_message(sock, request)
    server_answer = get_message(sock)
    if RESPONSE in server_answer and server_answer[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Ошибка удаления пользователя из списка контактов')


def database_init(sock, database, username):
    try:
        users_list = users_list_request(sock, username)
    except ServerError:
        CLIENT_LOGGER.error('Ошибка запроса списка активных пользователей.')
    else:
        database.init_active_users(users_list)

    try:
        contacts_list = contacts_list_request(sock, username)
    except ServerError:
        CLIENT_LOGGER.error('Ошибка запроса списка контактов.')
    else:
        for contact in contacts_list:
            database.add_contact(contact)


def main():
    request_address, request_port, request_name = arg_parser()

    if not request_name:
        request_name = input('Введите имя пользователя: ')

    CLIENT_LOGGER.info(f'Запущен клиент со следующими параметрами: '
                       f'адрес - {request_address}, порт - {request_port}, имя - {request_name}')

    print(f'Консольный мессенджер. Имя пользователя - {request_name}')

    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.settimeout(1)
        transport.connect((request_address, request_port))
        send_message(transport, user_request(request_name))
        response = server_response(get_message(transport))
        CLIENT_LOGGER.info(f'Ответ сервера принят: {response}')
    except ServerError as error:
        CLIENT_LOGGER.error(f'При установке соединения сервер вернул ошибку: {error.text}')
        sys.exit(1)
    except json.JSONDecodeError:
        CLIENT_LOGGER.error('Не удалось декодировать сообщение сервера.')
        sys.exit(1)
    except ReqFieldMissingError as missing_error:
        CLIENT_LOGGER.error(f'В ответе сервера отсутствует необходимое поле '
                            f'{missing_error.missing_field}')
        sys.exit(1)
    except ConnectionRefusedError:
        CLIENT_LOGGER.critical('Отказ узла в попытке соединения')
        sys.exit(1)
    else:

        database = ClientDatabase(request_name)
        database_init(transport, database, request_name)

        listen_user = ClientReader(transport, request_name, database)
        listen_user.daemon = True
        listen_user.start()

        send_user = ClientSender(transport, request_name, database)
        send_user.daemon = True
        send_user.start()

        while True:
            time.sleep(1)
            if listen_user.is_alive() and send_user.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
