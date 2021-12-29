from PyQt5.QtWidgets import (QDialog, QFileDialog, QGridLayout, QLabel,
                             QLineEdit, QMessageBox, QPushButton, QSizePolicy)


class ConfigurationWindow(QDialog):
    """
    Класс - диалоговое окно настроек сервера.
    """
    def __init__(self, settings):
        super().__init__()
        self.settings = settings

        self.setFixedSize(self.sizeHint())
        self.setWindowTitle('Настройки сервера')

        self.db_path_label = QLabel('Путь до файла базы данных: ', self)
        self.db_file_label = QLabel('Имя файла базы данных: ', self)
        self.port_label = QLabel('Номер порта для соединений:', self)
        self.address_label = QLabel('С какого IP принимаем соединения:'
                                    '\n(оставьте это поле пустым, чтобы\n'
                                    'принимать соединения с любых адресов)', self)

        self.db_path_select = QPushButton('Обзор...', self)
        self.db_path_select.clicked.connect(self.open_file_dialog)
        self.db_path_select.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))

        self.save_btn = QPushButton('Сохранить', self)
        self.save_btn.clicked.connect(self.save_server_settings)
        self.save_btn.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))

        self.close_button = QPushButton('Закрыть', self)
        self.close_button.clicked.connect(self.close)
        self.close_button.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))

        self.db_path = QLineEdit(self)
        self.db_file = QLineEdit(self)
        self.port = QLineEdit(self)
        self.address = QLineEdit(self)

        grid = QGridLayout()
        grid.setColumnStretch(1, 2)
        grid.setSpacing(20)

        grid.addWidget(self.db_path_label, 0, 0, 1, 2)

        grid.addWidget(self.db_path, 1, 0, 1, 2)
        grid.addWidget(self.db_path_select, 1, 2, 1, 1)

        grid.addWidget(self.db_file_label, 2, 0, 1, 1)
        grid.addWidget(self.db_file, 2, 1, 1, 2)

        grid.addWidget(self.port_label, 3, 0, 1, 1)
        grid.addWidget(self.port, 3, 1, 1, 2)

        grid.addWidget(self.address_label, 4, 0, 2, 1)
        grid.addWidget(self.address, 4, 1, 2, 2)

        grid.addWidget(self.save_btn, 6, 1, 1, 1)
        grid.addWidget(self.close_button, 6, 2, 1, 1)

        self.setLayout(grid)

        self.db_path.insert(self.settings['SETTINGS']['Database_path'])
        self.db_file.insert(self.settings['SETTINGS']['Database_file'])
        self.port.insert(self.settings['SETTINGS']['Default_port'])
        self.address.insert(self.settings['SETTINGS']['Listen_address'])

    def open_file_dialog(self):
        """
        Метод-обработчик открытия окна выбора папки.

        :return: ничего не возвращает.
        """
        dialog = QFileDialog(self)
        path = dialog.getExistingDirectory()
        path = path.replace('/', '\\')
        self.db_path.clear()
        self.db_path.insert(path)

    def save_server_settings(self):
        """
        Метод, сохраняющий настройки сервера.
        Проверяет правильность введенных данных, и при корректности данных
        сохраняет их в server.ini файл серверной папки.

        :return: ничего не возвращает.
        """
        message = QMessageBox()
        self.settings['SETTINGS']['Database_path'] = self.db_path.text()
        self.settings['SETTINGS']['Database_file'] = self.db_file.text()
        try:
            port = int(self.port.text())
        except ValueError:
            message.warning(self, 'Error', 'Порт должен быть числом')
        else:
            self.settings['SETTINGS']['Listen_address'] = self.address.text()
            if 1023 < port < 65536:
                self.settings['SETTINGS']['Default_port'] = str(port)
                with open('server.ini', 'w') as conf:
                    self.settings.write(conf)
                    message.information(self, 'Successful', 'Настройки успешно сохранены!')
            else:
                message.warning(self, 'Error', 'Порт должен быть в диапазоне от 1024 до 65536')
