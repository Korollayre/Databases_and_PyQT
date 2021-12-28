import dis


class ClientVerifier(type):
    """
    Метакласс, проверяющий что в результирующем классе нет серверных
    вызовов таких как: accept, listen. Также проверяется, что сокет не
    создаётся внутри конструктора класса.
    """

    def __init__(cls, clsname, bases, clsdict):
        super().__init__(clsname, bases, clsdict)
        methods = []
        for item in clsdict:
            try:
                func = dis.get_instructions(clsdict[item])
            except TypeError:
                pass
            else:
                for el in func:
                    if el.opname == 'LOAD_GLOBAL':
                        if el.argval not in methods:
                            methods.append(el.argval)

        for command in ('accept', 'listen', 'socket'):
            if command in methods:
                raise TypeError('В классе обнаружено использование запрещённого метода')
        if 'get_message' in methods or 'send_message' in methods:
            pass
        else:
            raise TypeError('Отсутствуют вызовы функций, работающих с сокетами.')
