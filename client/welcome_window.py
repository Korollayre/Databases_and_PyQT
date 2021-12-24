import sys

from PyQt5.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLabel,
                             QLineEdit, QMessageBox, QPushButton, QVBoxLayout,
                             qApp)


class WelcomeWindow(QDialog):
    def __init__(self):
        super(WelcomeWindow, self).__init__()
        self.enter_button_pressed = False
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Привет!')

        self.message = QMessageBox()
        self.message.setIcon(QMessageBox.Information)
        self.message.setWindowTitle('Ошибка!')
        self.message.setText('Вы не ввели имя пользователя!')

        self.setFixedSize(230, 150)

        self.username_label = QLabel('Введите имя пользователя:', self)
        self.user_password_label = QLabel('Введите пароль:', self)

        self.username_filed = QLineEdit(self)
        self.user_password = QLineEdit(self)
        self.user_password.setEchoMode(QLineEdit.Password)

        self.close_button = QPushButton('Выйти', self)
        self.close_button.clicked.connect(qApp.exit)

        self.enter_button = QPushButton('Войти', self)
        self.enter_button.clicked.connect(self.enter_button_click)

        mainLayout = QVBoxLayout()
        buttonLayout = QHBoxLayout()

        mainLayout.setSpacing(10)

        mainLayout.addWidget(self.username_label)
        mainLayout.addWidget(self.username_filed)
        mainLayout.addWidget(self.user_password_label)
        mainLayout.addWidget(self.user_password)

        buttonLayout.addWidget(self.enter_button)
        buttonLayout.addWidget(self.close_button)
        mainLayout.addLayout(buttonLayout)

        self.setLayout(mainLayout)
        self.show()

    def enter_button_click(self):
        if self.username_filed.text():
            self.enter_button_pressed = True
            qApp.exit()
        else:
            self.message.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = WelcomeWindow()

    app.exec_()
