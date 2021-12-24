import binascii
import hashlib

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QGridLayout, QHBoxLayout, QLabel,
                             QLineEdit, QMessageBox, QPushButton, QSizePolicy,
                             QVBoxLayout)


class RegisterUser(QDialog):
    def __init__(self, database, server):
        super(RegisterUser, self).__init__()
        self.database = database
        self.server = server
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Регистрация')

        self.setFixedSize(400, 180)
        self.setModal(True)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.messages = QMessageBox()

        self.username_label = QLabel('Введите имя пользователя:', self)
        self.password_label = QLabel('Введите пароль:', self)
        self.confirm_label = QLabel('Подтвердите пароль:', self)

        self.register_button = QPushButton('Сохранить', self)
        self.register_button.clicked.connect(self.registration)
        self.register_button.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))

        self.close_button = QPushButton('Закрыть', self)
        self.close_button.clicked.connect(self.close)
        self.close_button.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))

        self.username = QLineEdit()

        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)

        self.confirm = QLineEdit()
        self.confirm.setEchoMode(QLineEdit.Password)

        grid = QGridLayout()
        grid.setColumnStretch(1, 2)
        grid.setSpacing(20)

        grid.addWidget(self.username_label, 0, 0, 1, 1)
        grid.addWidget(self.username, 0, 1, 1, 2)

        grid.addWidget(self.password_label, 1, 0, 1, 1)
        grid.addWidget(self.password, 1, 1, 1, 2)

        grid.addWidget(self.confirm_label, 2, 0, 1, 1)
        grid.addWidget(self.confirm, 2, 1, 1, 2)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.register_button)
        button_layout.addWidget(self.close_button)

        main_layout = QVBoxLayout()
        main_layout.addLayout(grid)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def registration(self):
        if not self.username.text():
            self.messages.critical(
                self, 'Ошибка', 'Не указано имя пользователя.')
            return
        elif self.password.text() != self.confirm.text():
            self.messages.critical(
                self, 'Ошибка', 'Введённые пароли не совпадают.')
            return
        elif self.database.check_user(self.username.text()):
            self.messages.critical(
                self, 'Ошибка', 'Пользователь уже существует.')
            return
        else:
            password_bytes = self.password.text().encode('utf-8')
            salt = self.username.text().lower().encode('utf-8')
            password_hash = hashlib.pbkdf2_hmac('sha512', password_bytes, salt, 10000)
            self.database.user_registration(self.username.text(), binascii.hexlify(password_hash))
            self.messages.information(self, 'Успех', 'Пользователь успешно зарегистрирован.')
            self.server.service_update_lists()
            self.close()

