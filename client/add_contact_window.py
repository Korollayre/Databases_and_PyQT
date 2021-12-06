import logging
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QLabel, QDialog, QPushButton, \
    QGridLayout, QComboBox

CLIENT_LOGGER = logging.getLogger('client')


class AddContactWindow(QDialog):
    def __init__(self, transport, database):
        super(AddContactWindow, self).__init__()

        self.transport = transport
        self.database = database

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Добавление контакта')

        self.setFixedSize(400, 120)
        self.sizeHint()
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

        self.label = QLabel('Выберите контакт для добавления:')

        self.selector = QComboBox(self)

        self.selector.setFixedHeight(30)

        self.refresh_button = QPushButton('Обновить список', self)
        self.refresh_button.setFixedSize(100, 30)
        self.refresh_button.clicked.connect(self.update_contacts)

        self.add_button = QPushButton('Добавить', self)
        self.add_button.setFixedSize(100, 30)

        self.close_button = QPushButton('Выйти', self)
        self.close_button.setFixedSize(100, 30)
        self.close_button.clicked.connect(self.close)

        grid = QGridLayout()
        print(grid.getContentsMargins())
        grid.setVerticalSpacing(20)
        grid.addWidget(self.label, 0, 0, 1, 3)

        # selector_layout.setAlignment(Qt.Alignment(Qt.AlignCenter))
        grid.addWidget(self.selector, 1, 0, 1, 3)
        grid.addWidget(self.refresh_button, 2, 1, 1, 2)

        grid.addWidget(self.add_button, 1, 3, 1, 1)
        grid.addWidget(self.close_button, 2, 3, 1, 1)

        grid.setContentsMargins(10, 10, 10, 20)

        self.setLayout(grid)

        self.possible_contacts_list()

    def possible_contacts_list(self):
        self.selector.clear()

        contacts_list = set(self.database.get_contacts())
        users_list = set(self.database.get_users())

        users_list.remove(self.transport.name)

        self.selector.addItems(users_list - contacts_list)

    def update_contacts(self):
        try:
            self.transport.users_list_update()
        except OSError:
            pass
        else:
            CLIENT_LOGGER.info('Выполнение обновление списка возможных контактов по запросу пользователя.')
            self.possible_contacts_list()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AddContactWindow(1, 2)

    app.exec_()
