import logging

from PyQt5.QtCore import Qt, QEvent, pyqtSlot, QSortFilterProxyModel
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon
from PyQt5.QtWidgets import QMainWindow, QAction, QMessageBox, QMenu

from client.main_window_conv import Ui_MainClientWindow
from errors import ServerError

CLIENT_LOGGER = logging.getLogger('client')


class MainWindow(QMainWindow):
    def __init__(self, database, transport):
        super(MainWindow, self).__init__()

        self.database = database
        self.transport = transport

        self.initUI()

    def initUI(self):
        self.setFixedSize(self.sizeHint())
        self.setWindowTitle(f'Client {self.transport.username} GUI')

        self.ui = Ui_MainClientWindow()
        self.ui.setupUi(self)

        self.ui.send_button.setIcon(QIcon('img/send.png'))
        self.ui.send_button.clicked.connect(self.send_message)

        self.ui.users_list.installEventFilter(self)
        self.ui.contacts_list.installEventFilter(self)

        self.ui.menu_exit.triggered.connect(self.close)

        self.users_model = None
        self.contacts_model = None
        self.messages_history_model = None
        self.current_chat = None

        self.messages = QMessageBox()
        self.ui.messages_list.setWordWrap(True)

        self.ui.contacts_list.doubleClicked.connect(self.select_active_chat)
        self.ui.users_list.doubleClicked.connect(self.select_active_chat)

        self.users_list_update()
        self.contacts_list_update()
        self.set_input_disable()

        self.show()

    def eventFilter(self, source, event):
        menu = QMenu(self)

        self.add_contact_action = QAction('Добавить в контакты', self)
        self.remove_contact_action = QAction('Удалить из контактов', self)
        self.refresh_action = QAction('Обновить', self)

        menu.addAction(self.add_contact_action)
        menu.addAction(self.remove_contact_action)
        menu.addAction(self.refresh_action)

        self.refresh_action.triggered.connect(self.users_list_update)

        if event.type() == QEvent.ContextMenu and source is self.ui.users_list:
            self.remove_contact_action.setDisabled(True)

            if menu.exec_(event.globalPos()):
                user_item = source.currentIndex().data()
                if user_item:
                    self.add_contact_action.triggered.connect(lambda: self.add_contact(user_item))
                    self.add_contact_action.trigger()
            return True

        if event.type() == QEvent.ContextMenu and source is self.ui.contacts_list:
            self.add_contact_action.setDisabled(True)
            self.refresh_action.setDisabled(True)

            if menu.exec_(event.globalPos()):
                contact_item = source.currentIndex().data()
                if contact_item:
                    self.remove_contact_action.triggered.connect(lambda: self.remove_contact(contact_item))
                    self.add_contact_action.trigger()
            return True

        return super().eventFilter(source, event)

    def set_input_disable(self):
        self.ui.message_input.clear()
        self.ui.message_input.setPlaceholderText('Выберите пользователя для диалога')

        if self.messages_history_model:
            self.messages_history_model.clear()

        self.ui.send_button.setDisabled(True)
        self.ui.message_input.setDisabled(True)

    def laod_message_history(self):
        input_messages = self.database.get_user_messages_history(sender=self.transport.username,
                                                                 receiver=self.current_chat)
        output_messages = self.database.get_user_messages_history(receiver=self.transport.username,
                                                                  sender=self.current_chat)

        input_messages.extend(output_messages)

        if not input_messages:
            pass
        else:
            messages_list = sorted(input_messages, key=lambda message_time: message_time[3])

            if not self.messages_history_model:
                self.messages_history_model = QStandardItemModel()
                self.ui.messages_list.setModel(self.messages_history_model)

            self.messages_history_model.clear()

            length = len(messages_list)
            start_index = 0
            if length > 20:
                start_index = length - 20

            for i in range(start_index, length):
                item = messages_list[i]
                if item[1] == self.transport.username:
                    row = QStandardItem(
                        f'{self.transport.username} {item[3].strftime("%H:%M")}\n{item[2]}')
                    row.setEditable(False)
                    row.setTextAlignment(Qt.AlignRight)
                    self.messages_history_model.appendRow(row)
                else:
                    row = QStandardItem(
                        f'{self.current_chat} {item[3].strftime("%H:%M")}\n{item[2]}')
                    row.setEditable(False)
                    row.setTextAlignment(Qt.AlignLeft)
                    self.messages_history_model.appendRow(row)

            self.ui.messages_list.scrollToBottom()

    def select_active_chat(self):
        if self.ui.users_list.currentIndex().data():
            self.current_chat = self.ui.users_list.currentIndex().data()
        elif self.ui.contacts_list.currentIndex().data():
            self.current_chat = self.ui.contacts_list.currentIndex().data()

        self.set_active_chat()

    def set_active_chat(self):
        self.ui.converasation_label.setText(f'{self.current_chat}')
        self.ui.message_input.setPlaceholderText('Введите сообщение')

        self.ui.send_button.setDisabled(False)
        self.ui.message_input.setDisabled(False)

        self.laod_message_history()

    def users_list_update(self):
        self.transport.users_list_request()
        users_list = self.database.get_active_users()
        self.users_model = QStandardItemModel()

        for user in sorted(users_list):
            if user == self.transport.username:
                continue
            row = QStandardItem(user)
            row.setEditable(False)
            self.users_model.appendRow(row)

        users_filter_model = QSortFilterProxyModel()
        users_filter_model.setSourceModel(self.users_model)
        users_filter_model.setFilterKeyColumn(0)

        self.ui.users_search_field.textChanged.connect(users_filter_model.setFilterRegExp)

        self.ui.users_list.setModel(users_filter_model)

    def contacts_list_update(self):
        self.transport.contacts_list_request()
        contacts_list = self.database.get_user_contacts()
        self.contacts_model = QStandardItemModel()

        for contact in sorted(contacts_list):
            row = QStandardItem(contact)
            row.setEditable(False)
            self.contacts_model.appendRow(row)

        self.ui.contacts_list.setModel(self.contacts_model)

        contacts_filter_model = QSortFilterProxyModel()
        contacts_filter_model.setSourceModel(self.contacts_model)
        contacts_filter_model.setFilterKeyColumn(0)

        self.ui.contacts_search_field.textChanged.connect(contacts_filter_model.setFilterRegExp)

        self.ui.contacts_list.setModel(contacts_filter_model)

    def add_contact(self, username):
        try:
            self.transport.add_contact_to_server(username)
        except ServerError as error:
            self.messages.critical(self, 'Ошибка сервера', error.text)
        except OSError as error:
            if error.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения!')
        else:
            self.database.add_contact(username)
            row = QStandardItem(username)
            row.setEditable(False)
            self.contacts_model.appendRow(row)
            CLIENT_LOGGER.info(f'Пользователь {username} добавлен в контакты.')
            self.messages.information(self, 'Success', 'Контакт успешно добавлен.')
            self.contacts_list_update()

    def remove_contact(self, contact):
        try:
            self.transport.remove_contact_from_server(contact)
        except ServerError as error:
            self.messages.critical(self, 'Ошибка сервера', error.text)
        except OSError as error:
            if error.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения!')
        else:
            self.database.delete_contact(contact)
            self.users_list_update()
            CLIENT_LOGGER.info(f'Пользователь {contact} удален из контактов.')
            self.messages.information(self, 'Success', 'Контакт успешно удален.')
            self.contacts_list_update()

    def send_message(self):
        message_text = self.ui.message_input.toPlainText()
        self.ui.message_input.clear()
        if not message_text:
            return
        try:
            self.transport.create_user_message(self.current_chat, message_text)
        except ServerError as error:
            self.messages.critical(self, 'Ошибка', error.text)
        except OSError as error:
            if error.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения!')
        except (ConnectionResetError, ConnectionAbortedError):
            self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером!')
            self.close()
        else:
            self.database.save_user_message(self.transport.username, self.current_chat, message_text)
            CLIENT_LOGGER.debug(f'Отправлено сообщение {message_text} пользователю {self.current_chat}.')
            self.laod_message_history()

    @pyqtSlot(str)
    def message_receive(self, sender):
        if sender == self.current_chat:
            self.laod_message_history()
        else:
            if self.messages.question(self, 'Новое сообщение',
                                      f'Получено новое сообщение от пользователя {sender}. Открыть чат с ним?',
                                      QMessageBox.Yes, QMessageBox.No) == QMessageBox.Yes:
                self.current_chat = sender
                self.set_active_chat()

    @pyqtSlot()
    def connection_lost(self):
        self.messages.warning(self, 'Сбой соединения', 'Потеряно соединение с сервером. ')

        self.close()

    def make_connection(self, trans_obj):
        trans_obj.new_message_signal.connect(self.message_receive)
        trans_obj.connection_lost_signal.connect(self.connection_lost)
