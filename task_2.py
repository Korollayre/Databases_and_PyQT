"""
2. Написать функцию host_range_ping() для перебора ip-адресов из заданного диапазона.
Меняться должен только последний октет каждого адреса.
По результатам проверки должно выводиться соответствующее сообщение.
"""
from ipaddress import ip_address
from task_1 import host_ping


def host_range_ping():
    while True:
        try:
            first_address = ip_address(input('Введите начальный адрес: '))
            first_address_last_octet = int(str(first_address).split('.').pop())
            break
        except ValueError:
            print('Ошибка: Введён некорректный начальный IP-адрес.')

    while True:
        try:
            last_address = ip_address(input('Введите конечный адрес: '))
            last_address_last_octet = int(str(last_address).split('.').pop())
            break
        except ValueError:
            print('Ошибка: Введён некорректный конечный IP-адрес.')

    if str(first_address).split('.')[:3] == str(last_address).split('.')[:3] and last_address_last_octet <= 255:
        counts = last_address_last_octet - first_address_last_octet + 1
        addresses_list = [first_address + octet for octet in range(counts)]
        print()
        return host_ping(addresses_list)
    else:
        return print('Введены некорректные данные.')


if __name__ == '__main__':
    host_range_ping()
