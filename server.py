"""Программа-сервер"""
import select
import socket
import sys
import logging
import argparse
import time

import logs.server_log_config

from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, \
    PRESENCE, TIME, USER, ERROR, DEFAULT_PORT, MESSAGE, MESSAGE_TEXT, SENDER, DESTINATION, EXIT
from common.utils import get_message, send_message
from decos import Log

SERVER_LOGGER = logging.getLogger('server')


@Log()
def process_user_message(message, messages, user, users, names):
    """
    Обработчик сообщений от клиентов, принимает словарь -
    сообщение от клинта, проверяет корректность,
    возвращает словарь-ответ для клиента

    :param users:
    :param names:
    :param message:
    :param messages:
    :param user:
    :return:
    """
    SERVER_LOGGER.info(f'Разбор сообщения {message}.')
    if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
        if message[USER][ACCOUNT_NAME] not in names.keys():
            names[message[USER][ACCOUNT_NAME]] = user
            send_message(user, {RESPONSE: 200})
            SERVER_LOGGER.info(f'Зарегистрирован новый пользователь {user}.')
        else:
            send_message(user, {
                RESPONSE: 400,
                ERROR: 'Имя пользователя уже занято.'
            })
            SERVER_LOGGER.info(f'Попытка создания пользователя с существующим именем. Закрытие соединения.')
            users.remove(user)
            user.close()
        return
    elif ACTION in message and message[ACTION] == MESSAGE and DESTINATION in message and TIME in message \
            and SENDER in message and MESSAGE_TEXT in message:
        messages.append(message)
        SERVER_LOGGER.info(f'Добавление сообщения {message} в очередь.')
        return
    elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
        users.remove(names[message[ACCOUNT_NAME]])
        names[message[ACCOUNT_NAME]].close()
        del names[message[ACCOUNT_NAME]]
        SERVER_LOGGER.info(f'Завершение соединения по запросу пользователя.')
        return
    else:
        send_message(user, {
            RESPONSE: 400,
            ERROR: 'Bad Request'})
        return


@Log()
def process_message(message, names, listen_address):
    """
    Функция адресной отправки сообщения определённому клиенту. Принимает словарь сообщение,
    список зарегистрированых пользователей и слушающие сокеты. Ничего не возвращает.
    :param names:
    :param listen_address:
    :param message:
    :return:
    """
    if message[DESTINATION] in names and names[message[DESTINATION]] in listen_address:
        send_message(names[message[DESTINATION]], message)
        SERVER_LOGGER.info(
            f'Отправлено сообщение {message} пользователю {message[DESTINATION]} пользователем {message[SENDER]}.')
    elif message[DESTINATION] in names and names[message[DESTINATION]] not in listen_address:
        raise ConnectionError
    else:
        SERVER_LOGGER.error(f'Пользователь {message[DESTINATION]} не зарегистрирован. Отправка сообщения невозможна.')


@Log()
def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p

    if not 1023 < listen_port < 65536:
        SERVER_LOGGER.critical(f'Попытка запуска сервера с указанием неподходящего порта {listen_port}')
        sys.exit(1)

    return listen_address, listen_port


def main():
    """
    Загрузка параметров командной строки, если нет параметров, то задаём значения по умоланию.
    Сначала обрабатываем порт:
    server.py -p 8888 -a 127.0.0.1
    :return:
    """

    listen_address, listen_port = arg_parser()

    SERVER_LOGGER.info(f'Сервер запущен. Порт для подключения: {listen_port}, адрес: {listen_address}. '
                       f'При отсутствии адреса сервер принимает соединения со любых адресов')
    # Готовим сокет
    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.bind((listen_address, listen_port))
    transport.settimeout(1)

    SERVER_LOGGER.info(f'Настройка сокета завершена.')

    clients_list, messages_list, names = [], [], {}

    # Слушаем порт
    transport.listen(MAX_CONNECTIONS)

    while True:
        try:
            user, user_address = transport.accept()
        except OSError:
            pass
        else:
            SERVER_LOGGER.info(f'Соединение с {user_address} установлено')
            clients_list.append(user)

        recv_sockets_list, send_sockets_list, errors_sockets_list = [], [], []

        try:
            if clients_list:
                recv_sockets_list, send_sockets_list, errors_sockets_list = select.select(clients_list, clients_list,
                                                                                          [], 0)
        except OSError:
            pass
        if recv_sockets_list:
            for sender in recv_sockets_list:
                try:
                    process_user_message(get_message(sender), messages_list, sender, clients_list, names)
                except Exception:
                    SERVER_LOGGER.info(f'Соединение с {sender.getpeername()} разорвано.')
                    sender.close()
                    clients_list.remove(sender)

        for message in messages_list:
            try:
                process_message(message, names, send_sockets_list)
            except Exception:
                SERVER_LOGGER.info(f'Соединение с клиентом {message[DESTINATION]} разорвана.')
                clients_list.remove(names[message[DESTINATION]])
                del names[message[DESTINATION]]
        messages_list.clear()


if __name__ == '__main__':
    main()
