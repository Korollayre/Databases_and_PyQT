from PyQt5.QtWidgets import QApplication, QLabel, QDialog, QPushButton, \
    QLineEdit, QVBoxLayout, QHBoxLayout, QMessageBox

import sys


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

        self.setFixedSize(230, 100)

        self.username_label = QLabel('Введите имя пользователя:', self)

        self.username_filed = QLineEdit(self)

        self.close_button = QPushButton('Выйти', self)
        self.close_button.clicked.connect(self.close)

        self.enter_button = QPushButton('Войти', self)
        self.enter_button.clicked.connect(self.enter_button_click)

        mainLayout = QVBoxLayout()
        buttonLayout = QHBoxLayout()

        mainLayout.setSpacing(10)

        mainLayout.addWidget(self.username_label)
        mainLayout.addWidget(self.username_filed)

        buttonLayout.addWidget(self.enter_button)
        buttonLayout.addWidget(self.close_button)
        mainLayout.addLayout(buttonLayout)

        self.setLayout(mainLayout)
        self.show()

    def enter_button_click(self):
        if self.username_filed.text():
            self.enter_button_pressed = True
            self.close()
        else:
            self.message.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = WelcomeWindow()

    app.exec_()
