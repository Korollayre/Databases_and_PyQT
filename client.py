"""Программа-клиент"""

import sys
import json
import socket
import threading
import time
import logging
import argparse

from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, \
    RESPONSE, ERROR, DEFAULT_IP_ADDRESS, DEFAULT_PORT, SENDER, MESSAGE, MESSAGE_TEXT, EXIT, DESTINATION
from common.utils import get_message, send_message
from errors import ReqFieldMissingError, ServerError, IncorrectDataRecivedError
from decos import Log

CLIENT_LOGGER = logging.getLogger('client')


@Log()
def create_exit_message(account_name):
    return {
        ACTION: EXIT,
        TIME: time.time(),
        DESTINATION: account_name
    }


def help_messages():
    print("Поддерживаемые команды: \n"
          "'message' - отправить сообщение.\n"
          "'help' - вызов справки.\n"
          "'exit' - завершение работы программы.")


@Log()
def message_handler(request_socket, request_username):
    while True:
        try:
            message = get_message(request_socket)
            if ACTION in message and message[ACTION] == MESSAGE and SENDER in message and MESSAGE_TEXT in message \
                    and DESTINATION in message and message[DESTINATION] == request_username:
                print(f'\nПолучено сообщение: {message[MESSAGE_TEXT]}.\nОт пользователя {message[SENDER]}\n'
                      f'Введите команду: ')
                CLIENT_LOGGER.info(f'Получено сообщение {message[MESSAGE_TEXT]} от пользователя {message[SENDER]}')
            else:
                CLIENT_LOGGER.error(f'Получено некорректное сообщение: {message}')
        except IncorrectDataRecivedError:
            CLIENT_LOGGER.error(f'Не удалось декодировать полученное сообщение.')
        except (OSError, ConnectionError, ConnectionAbortedError,
                ConnectionResetError, json.JSONDecodeError):
            CLIENT_LOGGER.critical(f'Потеряно соединение с сервером.')
            sys.exit(1)


@Log()
def creat_user_message(request_socket, account_name):
    receiver = input('Введите имя получателя: ')
    message = input('Введите сообщение: ')
    user_message = {
        ACTION: MESSAGE,
        SENDER: account_name,
        DESTINATION: receiver,
        TIME: time.time(),
        MESSAGE_TEXT: message
    }
    CLIENT_LOGGER.info(f'Сформировано сообщение {user_message}.')
    try:
        send_message(request_socket, user_message)
        CLIENT_LOGGER.info(f'Сообщение {user_message} пользователю {receiver} отправлено.')
    except Exception:
        CLIENT_LOGGER.critical(f'Потеряно соединение с сервером.')
        sys.exit(1)


@Log()
def user_poll(request_sock, request_username):
    help_messages()
    while True:
        request = input('Введите команду: ').strip()
        if request == 'message':
            creat_user_message(request_sock, request_username)
        elif request == 'help':
            help_messages()
        elif request == 'exit':
            send_message(request_sock, create_exit_message(request_username))
            print('Закрытие соединения.')
            CLIENT_LOGGER.info('Закрытие соединения по запросу пользователя.')
            time.sleep(1)
            break
        else:
            print("Не удалось распознать команду. Попробуйте снова (для вызова справки введите 'help').")


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


def main():
    request_address, request_port, request_name = arg_parser()

    if not request_name:
        request_name = input('Введите имя пользователя: ')

    CLIENT_LOGGER.info(f'Запущен клиент со следующими параметрами: '
                       f'адрес - {request_address}, порт - {request_port}, имя - {request_name}')

    print(f'Консольный мессенджер. Имя пользователя - {request_name}')

    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.connect((request_address, request_port))
        send_message(transport, user_request(request_name))
        response = server_response(get_message(transport))
        CLIENT_LOGGER.info(f'Ответ сервера принят: {response}')
        print(response)
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

        listen_user = threading.Thread(target=message_handler, args=(transport, request_name))
        listen_user.daemon = True
        listen_user.start()

        send_user = threading.Thread(target=user_poll, args=(transport, request_name))
        send_user.daemon = True
        send_user.start()

        while True:
            time.sleep(1)
            if listen_user.is_alive() and send_user.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
