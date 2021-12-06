import logging
import sys

import logs.client_log_config

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QLabel, QDialog, QPushButton, \
    QGridLayout, QComboBox

CLIENT_LOGGER = logging.getLogger('client')


class RemoveContactWindow(QDialog):
    def __init__(self, database):
        super(RemoveContactWindow, self).__init__()

        self.database = database

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Удаление контактов')

        self.setFixedSize(400, 120)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

        self.label = QLabel('Выберите контакт для удаления:')

        self.selector = QComboBox(self)
        self.selector.setFixedHeight(30)

        self.remove_button = QPushButton('Удалить', self)
        self.remove_button.setFixedSize(100, 30)

        self.close_button = QPushButton('Выйти', self)
        self.close_button.setFixedSize(100, 30)
        self.close_button.clicked.connect(self.close)

        grid = QGridLayout()

        grid.addWidget(self.label, 0, 0, 1, 3)

        grid.addWidget(self.selector, 1, 0, 1, 4)
        grid.addWidget(self.remove_button, 1, 4, 1, 1)

        grid.addWidget(self.close_button, 2, 2, 1, 2)

        self.setLayout(grid)

        self.selector.addItems(sorted(self.database.get_user_contacts()))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RemoveContactWindow(1)
    app.exec_()
