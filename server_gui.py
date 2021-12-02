from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, QLabel, QTableView, QDialog, QPushButton, \
    QLineEdit, QFileDialog, QDesktopWidget, QWidget, QGridLayout, QVBoxLayout, QHBoxLayout, QSizePolicy
from PyQt5.QtGui import QStandardItemModel, QStandardItem

import sys


def active_users_table_create(database):
    users_list = database.active_users_list()
    model = QStandardItemModel()
    model.setHorizontalHeaderLabels(['Имя пользователя', 'IP-адрес', 'Порт подключения', 'Время подключения', ])
    for row in users_list:
        username, address, port, time = row

        username = QStandardItem(username)
        username.setEditable(False)

        address = QStandardItem(address)
        address.setEditable(False)

        port = QStandardItem(str(port))
        port.setEditable(False)

        time = QStandardItem(str(time.replace(microsecond=0)))
        time.setEditable(False)

        model.appendRow([username, address, port, time])
    return model


def users_history_table_create(database, username=None):
    if username:
        history = database.message_history(username)
    else:
        history = database.message_history()

    model = QStandardItemModel()
    model.setHorizontalHeaderLabels(
        ['Имя пользователя', 'Последний вход', 'Сообщений отправлено', 'Сообщений принято'])
    for row in history:
        username, last_login, sent, received = row

        username = QStandardItem(username)
        username.setEditable(False)

        last_login = QStandardItem(str(last_login.replace(microsecond=0)))
        last_login.setEditable(False)

        sent = QStandardItem(str(sent))
        sent.setEditable(False)

        received = QStandardItem(str(received))
        received.setEditable(False)

        model.appendRow([username, last_login, sent, received])
    return model


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        exit_action = QAction('Выход', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(qApp.quit)

        self.toolbar = self.addToolBar('ToolBar')

        self.history_view_button = QAction('История клиентов', self)
        self.configuration_button = QAction('Настройки сервера', self)
        self.refresh_button = QAction('Обновить список клиентов', self)

        self.toolbar.addAction(exit_action)
        self.toolbar.addAction(self.refresh_button)
        self.toolbar.addAction(self.configuration_button)
        self.toolbar.addAction(self.history_view_button)

        self.setMinimumHeight(300)

        self.resize(self.sizeHint().width(), self.minimumHeight())
        self.setWindowTitle('Buinichenko Mikhail server GUI')

        self.label = QLabel('Список подключенных клиентов:', self)
        self.label.adjustSize()

        self.active_clients_table = QTableView(self)

        window = QWidget()

        verticalLayout = QVBoxLayout()
        horizontalLayout = QHBoxLayout()

        horizontalLayout.addWidget(self.active_clients_table)
        verticalLayout.addWidget(self.label)
        verticalLayout.addLayout(horizontalLayout)

        window.setLayout(verticalLayout)

        self.setCentralWidget(window)
        self.show()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


class HistoryWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Клиентская история')

        self.setMinimumHeight(300)

        self.resize(self.sizeHint().width(), self.minimumHeight())

        self.history_table = QTableView(self)

        self.close_button = QPushButton('Закрыть', self)
        self.close_button.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.close_button.clicked.connect(self.close)

        mainLayout = QVBoxLayout()
        buttonLayout = QHBoxLayout()

        buttonLayout.addWidget(self.close_button)
        mainLayout.addWidget(self.history_table)
        mainLayout.addLayout(buttonLayout)

        self.setLayout(mainLayout)

        self.show()


class ConfigurationWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # self.setFixedSize(500, 300)
        self.setFixedSize(self.sizeHint())
        # self.resize(self.sizeHint())
        self.setWindowTitle('Настройки сервера')

        self.db_path_label = QLabel('Путь до файла базы данных: ', self)
        self.db_file_label = QLabel('Имя файла базы данных: ', self)
        self.port_label = QLabel('Номер порта для соединений:', self)
        self.address_label = QLabel('С какого IP принимаем соединения:'
                                    '\n(оставьте это поле пустым, чтобы\n'
                                    'принимать соединения с любых адресов)', self)

        self.db_path_select = QPushButton('Обзор...', self)
        self.db_path_select.clicked.connect(self.open_file_dialog)
        self.db_path_select.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))

        self.save_btn = QPushButton('Сохранить', self)
        self.save_btn.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))

        self.close_button = QPushButton('Закрыть', self)
        self.close_button.clicked.connect(self.close)
        self.close_button.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))

        self.db_path = QLineEdit(self)
        self.db_file = QLineEdit(self)
        self.port = QLineEdit(self)
        self.address = QLineEdit(self)

        grid = QGridLayout()
        grid.setColumnStretch(1, 2)
        grid.setSpacing(20)

        grid.addWidget(self.db_path_label, 0, 0, 1, 2)

        grid.addWidget(self.db_path, 1, 0, 1, 2)
        grid.addWidget(self.db_path_select, 1, 2, 1, 1)

        grid.addWidget(self.db_file_label, 2, 0, 1, 1)
        grid.addWidget(self.db_file, 2, 1, 1, 2)

        grid.addWidget(self.port_label, 3, 0, 1, 1)
        grid.addWidget(self.port, 3, 1, 1, 2)

        grid.addWidget(self.address_label, 4, 0, 2, 1)
        grid.addWidget(self.address, 4, 1, 2, 2)

        grid.addWidget(self.save_btn, 6, 1, 1, 1)
        grid.addWidget(self.close_button, 6, 2, 1, 1)

        self.setLayout(grid)
        self.show()

    def open_file_dialog(self):
        dialog = QFileDialog(self)
        path = dialog.getExistingDirectory()
        path = path.replace('/', '\\')
        self.db_path.insert(path)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ConfigurationWindow()

    app.exec_()
