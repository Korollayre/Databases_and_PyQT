import dis


class ServerVerifier(type):
    """
    Метакласс, проверяющий что в результирующем классе нет клиентских
    вызовов таких как: connect. Также проверяется, что серверный
    сокет является TCP и работает по IPv4 протоколу.
    """
    def __init__(cls, clsname, bases, clsdict):
        super().__init__(clsname, bases, clsdict)
        methods = []
        attrs = []
        for item in clsdict:
            try:
                func = dis.get_instructions(clsdict[item])
            except (TypeError, IndentationError):
                pass
            else:
                for el in func:
                    if el.opname == 'LOAD_GLOBAL':
                        if el.argval not in methods:
                            methods.append(el.argval)
                    elif el.opname == 'LOAD_ATTR':
                        if el.argval not in attrs:
                            attrs.append(el.argval)

        if 'connect' in methods:
            raise TypeError('Использование метода connect недопустимо.')
        if not ('SOCK_STREAM' in attrs and 'AF_INET' in attrs):
            raise TypeError('Некорректная инициализация сокета.')
