import sys

from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (QAction, QApplication, QDesktopWidget, QDialog,
                             QFileDialog, QGridLayout, QHBoxLayout, QLabel,
                             QLineEdit, QMainWindow, QPushButton, QSizePolicy,
                             QTableView, QVBoxLayout, QWidget, qApp)


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
        self.setMinimumWidth(500)
        self.resize(self.minimumWidth(), self.minimumHeight())
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

