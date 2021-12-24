import subprocess


def main():
    process = []
    venv_path = '../venv/Scripts/python'
    while True:
        ACTION = input("Для запуска сервера и клиентов введите 's', для выхода - 'q', для закрытия всех окон 'x': ")

        if ACTION == 'q':
            break
        elif ACTION == 's':
            # users = int(input('Введите количество клиентов для запуска: '))

            process.append(
                subprocess.Popen(f'{venv_path} server.py', creationflags=subprocess.CREATE_NO_WINDOW))

            for i in range(3):
                process.append(
                    subprocess.Popen(f'{venv_path} client.py -n test{i + 1} -p password',
                                     creationflags=subprocess.CREATE_NO_WINDOW))

        elif ACTION == 'x':
            while process:
                victim = process.pop()
                victim.kill()


if __name__ == '__main__':
    main()
