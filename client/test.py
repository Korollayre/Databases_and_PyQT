from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys


class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        # setting title
        self.setWindowTitle("Python ")

        # setting geometry
        self.setGeometry(100, 100, 600, 400)

        # calling method
        self.UiComponents()

        # showing all the widgets
        self.show()

    # method for widgets
    def UiComponents(self):
        # creating a push button
        button = QPushButton(self)

        # setting geometry of button
        # button.setFixedSize(button.sizeHint())

        # setting icon to the button
        button.setIcon(QIcon('img/send.png'))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Window()

    app.exec_()