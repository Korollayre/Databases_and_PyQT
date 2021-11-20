"""
1. Написать функцию host_ping(), в которой с помощью утилиты ping будет проверяться доступность сетевых узлов.
Аргументом функции является список, в котором каждый сетевой узел должен быть представлен именем хоста или ip-адресом.
В функции необходимо перебирать ip-адреса и проверять их доступность с выводом соответствующего сообщения:
(«Узел доступен», «Узел недоступен»).
При этом ip-адрес сетевого узла должен создаваться с помощью функции ip_address().
"""

from ipaddress import ip_address
from subprocess import Popen, PIPE
import socket


def host_ping(addresses_list):
    res = {'Доступные узлы': [], 'Недоступные узлы': []}
    for address in addresses_list:
        try:
            ipv4_address = ip_address(address)
        except ValueError:
            ipv4_address = ip_address(socket.gethostbyname(address))
        p = Popen(f'ping {ipv4_address} -w 1000 -n 1', stdout=PIPE)
        p.wait()
        if p.returncode == 0:
            res['Доступные узлы'].append(address)
            print(f'Узел {address} доступен')
        else:
            res['Недоступные узлы'].append(address)
            print(f'Узел {address} недоступен')
    return res


if __name__ == '__main__':
    host_ping(['192.168.0.1', 'google.com', 'python.org', '8.8.8.8'])
