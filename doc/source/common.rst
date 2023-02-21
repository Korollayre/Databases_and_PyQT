Common package
===============

Пакет общих утилит, использующихся в разных модулях проекта.

Модуль decos.py
---------------

.. automodule:: common.decos
    :members:

Модуль descriptors.py
---------------------

.. automodule:: common.descriptors
    :members:

Модуль errors.py
----------------

.. automodule:: common.errors
    :members:

Модуль metaclasses.py
---------------------

.. automodule:: common.metaclasses
    :members:

Модуль utils.py
---------------

common.utils. **get_message** (*client*):
    Функция приёма сообщений от удалённых компьютеров.
    Принимает сообщения JSON, декодирует полученное сообщение
    и проверяет что получен словарь.

        :Параметры:
            **client** - сокет для передачи данных.

        :Результат:
            словарь - сообщение.

common.utils. **send_message** (*sock*, *message*):
    Функция отправки словарей через сокет.
    Кодирует словарь в формат JSON и отправляет через сокет.

        :Параметры:
            * **sock** - для передачи данных
            * **message** - словарь для передачи

        :Результат:
            ничего не возвращает

Модуль variables.py
-------------------

.. automodule:: common.variables
    :members:
