import sys

from PyQt5.QtCore import QSortFilterProxyModel
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (QAction, QApplication, QDesktopWidget, QDialog,
                             QFileDialog, QGridLayout, QHBoxLayout, QLabel,
                             QLineEdit, QMainWindow, QPushButton, QSizePolicy,
                             QTableView, QVBoxLayout, QWidget, qApp, QHeaderView, QMessageBox)


class RemoveUser(QDialog):
    def __init__(self, database, server):
        super(RemoveUser, self).__init__()
        self.database = database
        self.server = server
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Удаление пользователя')

        self.messages = QMessageBox()

        self.setMinimumHeight(650)
        self.setMinimumWidth(300)
        self.resize(self.minimumWidth(), self.minimumHeight())

        self.users_table = QTableView(self)
        self.users_table.doubleClicked.connect(self.remove_user)

        self.search_field = QLineEdit(self)
        self.search_field.setPlaceholderText('Введите имя пользователя для сортировки')

        self.close_button = QPushButton('Закрыть', self)
        self.close_button.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.close_button.clicked.connect(self.close)

        mainLayout = QVBoxLayout()
        buttonLayout = QHBoxLayout()

        buttonLayout.addWidget(self.close_button)
        mainLayout.addWidget(self.search_field)
        mainLayout.addWidget(self.history_table)
        mainLayout.addLayout(buttonLayout)

        self.setLayout(mainLayout)

        self.users_table_create()

        self.show()

    def remove_user(self):
        current_user = self.users_table.currentIndex().data()
        if self.messages.question(self, 'Удаление пользователя',
                                  f'Удалить пользователя {current_user}?', QMessageBox.Yes,
                                  QMessageBox.No) == QMessageBox.Yes:
            self.database.remove_user(current_user)
            if current_user in self.server.names:
                sock = self.server.names[current_user]
                del self.server.names[current_user]
                self.server.remove_client(sock)
            self.server.service_update_lists()
            self.close()

    def users_table_create(self):
        users = self.database.users_list()

        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(
            ['Имя пользователя', 'Последний вход'])

        for row in users:
            username, last_login = row

            username = QStandardItem(username)
            username.setEditable(False)

            last_login = QStandardItem(str(last_login.replace(microsecond=0)))
            last_login.setEditable(False)

            model.appendRow([username, last_login])

        self.users_table.setModel(model)

        self.filter_model = QSortFilterProxyModel()
        self.filter_model.setSourceModel(model)
        self.filter_model.setFilterKeyColumn(0)

        self.search_field.textChanged.connect(self.filter_model.setFilterRegExp)

        self.history_table.setModel(self.filter_model)

        self.users_table_headers = self.users_table.horizontalHeader()
        self.users_table_headers.setSectionResizeMode(0, QHeaderView.Stretch)
        self.users_table_headers.setSectionResizeMode(1, QHeaderView.Stretch)
        self.users_table_headers.setSectionResizeMode(2, QHeaderView.Stretch)
        self.users_table_headers.setSectionResizeMode(3, QHeaderView.Stretch)
