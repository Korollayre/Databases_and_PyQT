"""
Модуль запуска нескольких клиентов одновременно.

Использование:

После запуска будет выведено приглашение ввести команду.
Поддерживаемые команды:

1. s - Запустить сервер.

* Запускает сервер с настройками по умолчанию.

2. k - Запустить клиентов.

* Всего будет запущено 3 клиента.
* Клиенты будут запущены с именами вида **test1 - testX** и паролями **password**.
* Тестовых пользователей необходимо предварительно, вручную зарегистрировать на сервере с паролем **password**.
* Если клиенты запускаются впервые, время запуска может быть достаточно продолжительным из-за генерации новых RSA ключей.

3. x - Закрыть все окна.

* Закрывает все активные окна, которые были запущенны из данного модуля.

4. q - Завершить работу модуля.

* Завершает работу модуля
"""
import subprocess


def main():
    process = []
    venv_path = '../venv/Scripts/python'
    clients_online = False
    while True:
        command = input("Для запуска сервера и клиентов введите 's', для выхода - 'q', для закрытия всех окон 'x': ")

        if command == 'q':
            break
        elif command == 's':
            process.append(
                subprocess.Popen(f'{venv_path} server.py', creationflags=subprocess.CREATE_NO_WINDOW))
        elif command == 'k':
            if not clients_online:
                for i in range(3):
                    process.append(
                        subprocess.Popen(f'{venv_path} client.py -n test{i + 1} -p password',
                                         creationflags=subprocess.CREATE_NO_WINDOW))
                    clients_online = True
            else:
                print('Клиенты уже запущены.')

        elif command == 'x':
            while process:
                victim = process.pop()
                victim.kill()


if __name__ == '__main__':
    main()
