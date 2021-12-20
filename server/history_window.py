from PyQt5.QtCore import QSortFilterProxyModel
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (QDialog,
                             QHBoxLayout, QLineEdit, QPushButton, QSizePolicy,
                             QTableView, QVBoxLayout, QHeaderView)


class HistoryWindow(QDialog):
    def __init__(self, database):
        super().__init__()
        self.database = database
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Клиентская история')

        self.setMinimumHeight(300)
        self.setMinimumWidth(650)
        self.resize(self.minimumWidth(), self.minimumHeight())

        self.history_table = QTableView(self)

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

        self.users_history_table_create()

    def users_history_table_create(self):
        history = self.database.message_history()

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

        self.history_table.setModel(model)

        self.filter_model = QSortFilterProxyModel()
        self.filter_model.setSourceModel(model)
        self.filter_model.setFilterKeyColumn(0)

        self.search_field.textChanged.connect(self.filter_model.setFilterRegExp)

        self.history_table.setModel(self.filter_model)

        self.history_table_headers = self.history_table.horizontalHeader()
        self.history_table_headers.setSectionResizeMode(0, QHeaderView.Stretch)
        self.history_table_headers.setSectionResizeMode(1, QHeaderView.Stretch)
        self.history_table_headers.setSectionResizeMode(2, QHeaderView.Stretch)
        self.history_table_headers.setSectionResizeMode(3, QHeaderView.Stretch)
