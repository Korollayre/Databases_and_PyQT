import subprocess

PROCESSES = []

while True:
    ACTION = input("Для запуска сервера и клиентов введите 's', для выхода - 'q', для закрытия всех окон 'x': ")

    if ACTION == 'q':
        break
    elif ACTION == 's':
        PROCESSES.append(subprocess.Popen('python server.py',
                                          creationflags=subprocess.CREATE_NEW_CONSOLE))

        for i in range(4):
            PROCESSES.append(
                subprocess.Popen(f'python client.py --name test{i + 1}',
                                 creationflags=subprocess.CREATE_NEW_CONSOLE))

    elif ACTION == 'x':
        while PROCESSES:
            VICTIM = PROCESSES.pop()
            VICTIM.kill()
