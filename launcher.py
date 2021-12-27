"""
Модуль для запуска серверной и клиентской части
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
