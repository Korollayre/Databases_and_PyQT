from PyQt5.QtCore import QSortFilterProxyModel
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (QDialog, QHBoxLayout, QHeaderView, QLineEdit,
                             QMessageBox, QPushButton, QSizePolicy, QTableView,
                             QVBoxLayout)


class RemoveUser(QDialog):
    """
    Класс - диалоговое окно удаления пользователя с сервера.
    """

    def __init__(self, database, server):
        super(RemoveUser, self).__init__()
        self.database = database
        self.server = server

        self.setWindowTitle('Удаление пользователя')

        self.messages = QMessageBox()

        self.setMinimumHeight(500)
        self.setMinimumWidth(400)
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
        mainLayout.addWidget(self.users_table)
        mainLayout.addLayout(buttonLayout)

        self.setLayout(mainLayout)

        self.users_table_create()

    def remove_user(self):
        """
        Метод, осуществляющий удаление пользователя по двойному нажатию ЛКМ на его имя.

        :return: ничего не возвращает.
        """
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
            self.users_table_create()

    def users_table_create(self):
        """
        Метод, заполняющий таблицу зарегистрированных пользователей данными.

        :return: ничего не возвращает.
        """
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

        self.users_table.setModel(self.filter_model)

        self.users_table_headers = self.users_table.horizontalHeader()
        self.users_table_headers.setSectionResizeMode(0, QHeaderView.Stretch)
        self.users_table_headers.setSectionResizeMode(1, QHeaderView.Stretch)
