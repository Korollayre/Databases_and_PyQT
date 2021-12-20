"""Программа-сервер"""
import argparse
import configparser
import os
import select
import socket
import sys
from threading import Lock, Thread

from PyQt5.QtCore import QSortFilterProxyModel, QTimer, Qt
from PyQt5.QtWidgets import QApplication, QHeaderView, QMessageBox

from common.utils import get_message, send_message
from common.variables import *
from common.decos import Log
from common.descriptors import AddressVerifier, PortVerifier
from common.metaclasses import ServerVerifier
from server.server_database import ServerDatabase
from server.core import MessageProcessor
from server.main_window import (ConfigurationWindow, HistoryWindow, MainWindow)

SERVER_LOGGER = logging.getLogger('server')


@Log()
def arg_parser(default_port, default_address):
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=default_port, type=int, nargs='?')
    parser.add_argument('-a', default=default_address, nargs='?')
    parser.add_argument('--no_gui', action='store_true')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    gui_flag = namespace.no_gui

    return listen_address, listen_port, gui_flag


@Log()
def load_settings():
    settings = configparser.ConfigParser()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    settings.read(f'{dir_path}/server/server.ini')
    if 'SETTINGS' in settings:
        return settings
    else:
        settings.add_section('SETTINGS')
        settings.set('SETTINGS', 'Default_port', str(DEFAULT_PORT))
        settings.set('SETTINGS', 'Listen_Address', '')
        settings.set('SETTINGS', 'Database_path', '')
        settings.set('SETTINGS', 'Database_file', 'server_database.db3')
        return settings


def main():
    settings = load_settings()

    database = ServerDatabase(
        os.path.join(
            settings['SETTINGS']['Database_path'],
            settings['SETTINGS']['Database_file']))

    listen_address, listen_port, gui_flag = arg_parser(settings['SETTINGS']['Default_port'],
                                                       settings['SETTINGS']['Listen_Address'])

    server = MessageProcessor(listen_address, listen_port, database)
    server.daemon = True
    server.start()

    if gui_flag:
        while True:
            command = input('Введите exit для завершения работы сервера: ')
            if command == 'exit':
                server.running = False
                server.join()
                break
    else:
        app = QApplication(sys.argv)
        app.setAttribute(Qt.AA_DisableWindowContextHelpButton)
        window = MainWindow(database, server, settings)

        app.exec_()

        server.running = False


if __name__ == '__main__':
    main()
