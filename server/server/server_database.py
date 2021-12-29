from datetime import datetime

from sqlalchemy import (Column, DateTime, ForeignKey, Integer, MetaData,
                        String, Table, Text, create_engine)
from sqlalchemy.orm import mapper, sessionmaker
from sqlalchemy.sql import default_comparator


class ServerDatabase:
    """
    Класс-оболочка для работы с базой данных сервера.
    Использует SQLite базу данных, реализован с помощью
    SQLAlchemy ORM и используется классический подход.
    """

    class AllUsers:
        """
        Класс-отображения таблицы пользователей.
        """

        def __init__(self, username, password_hash):
            self.id = None
            self.pubkey = None
            self.username = username
            self.password_hash = password_hash
            self.last_login = datetime.now()

    class ActiveUsers:
        """
        Класс-отображения таблицы пользователей онлайн.
        """

        def __init__(self, user_id, address, port, login_time):
            self.id = None
            self.user = user_id
            self.address = address
            self.port: int = port
            self.login_time = login_time

    class LoginHistory:
        """
        Класс-отображения таблицы истории входа.
        """

        def __init__(self, user, date, address, port):
            self.id = None
            self.user = user
            self.date = date
            self.address = address
            self.port: int = port

    class UsersContacts:
        """
        Класс-отображения таблицы контактов пользователей.
        """

        def __init__(self, owner, contact):
            self.id = None
            self.owner = owner
            self.contact = contact

    class UsersMessagesHistory:
        """
        Класс-отображения таблицы статистики сообщений пользователей.
        """

        def __init__(self, user):
            self.id = None
            self.user = user
            self.sent: int = 0
            self.accepted: int = 0

    def __init__(self, path):
        self.database_engine = create_engine(f'sqlite:///{path}', echo=False, pool_recycle=7200,
                                             connect_args={'check_same_thread': False})

        self.metadata = MetaData()

        users_table = Table('Users', self.metadata,
                            Column('id', Integer, primary_key=True),
                            Column('pubkey', Text),
                            Column('username', String, unique=True),
                            Column('password_hash', String),
                            Column('last_login', DateTime),
                            )

        active_users_table = Table('ActiveUsers', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('user', ForeignKey('Users.id'), unique=True),
                                   Column('address', String),
                                   Column('port', Integer),
                                   Column('login_time', DateTime),
                                   )

        users_login_table = Table('LoginHistory', self.metadata,
                                  Column('id', Integer, primary_key=True),
                                  Column('user', ForeignKey('Users.id')),
                                  Column('date', DateTime),
                                  Column('address', String),
                                  Column('port', Integer),
                                  )

        users_contacts_table = Table('UsersContacts', self.metadata,
                                     Column('id', Integer, primary_key=True),
                                     Column('owner', ForeignKey('Users.id')),
                                     Column('contact', ForeignKey('Users.id')),
                                     )

        users_messages_history_table = Table('UsersMessageHistory', self.metadata,
                                             Column('id', Integer, primary_key=True),
                                             Column('user', ForeignKey('Users.id')),
                                             Column('sent', Integer),
                                             Column('accepted', Integer),
                                             )
        self.metadata.create_all(self.database_engine)

        mapper(self.AllUsers, users_table)
        mapper(self.ActiveUsers, active_users_table)
        mapper(self.LoginHistory, users_login_table)
        mapper(self.UsersContacts, users_contacts_table)
        mapper(self.UsersMessagesHistory, users_messages_history_table)

        session = sessionmaker(bind=self.database_engine)
        self.session = session()

        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    def user_registration(self, username, password_hash):
        """
        Метод, вызывающийся при регистрации пользователя. Принимает имя и хеш пароля,
        создает в БД записи в таблице пользователей и таблице статистики.

        :param username: имя пользователя.
        :param password_hash: хеш пароля.
        :return: ничего не возвращает.
        """
        user_instance = self.AllUsers(username, password_hash)
        self.session.add(user_instance)
        self.session.commit()

        user_messages_instance = self.UsersMessagesHistory(user_instance.id)
        self.session.add(user_messages_instance)
        self.session.commit()

    def remove_user(self, username):
        """
        Метод, осуществляющий удаление пользователя из базы данных.
        Удаляются все записи БД с текущим пользователем.

        :param username: имя пользователя.
        :return: ничего не возвращается.
        """
        user = self.session.query(self.AllUsers).filter_by(username=username).first()
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
        self.session.query(self.LoginHistory).filter_by(user=user.id).delete()
        self.session.query(self.UsersContacts).filter_by(owner=user.id).delete()
        self.session.query(self.UsersContacts).filter_by(contact=user.id).delete()
        self.session.query(self.UsersMessagesHistory).filter_by(user=user.id).delete()
        self.session.query(self.AllUsers).filter_by(username=username).delete()
        self.session.commit()

    def user_login(self, username, address, port, key):
        """
        Метод, вызывающийся при входе пользователя. Добавляет в базу запись о входе,
        обновляет открытый ключ пользователя при его изменении.

        :param username: имя пользователя.
        :param address: адрес, с которого осуществляется подключение.
        :param port: порт, с которого осуществляется подключение.
        :param key: открытый ключ пользователя.
        :return: ничего не возвращает.
        """
        query = self.session.query(self.AllUsers).filter_by(username=username)

        if query.count():
            user = query.first()
            user.last_login = datetime.now()
            if user.pubkey != key:
                user.pubkey = key
        else:
            raise ValueError('Пользователь не зарегистрирован.')

        new_active_user = self.ActiveUsers(user.id, address, port, datetime.now())
        self.session.add(new_active_user)

        user_history = self.LoginHistory(user.id, datetime.now(), address, port)
        self.session.add(user_history)

        self.session.commit()

    def message_exchange(self, sender, receiver):
        """
        Метод, осуществляющий изменение счетчика принятых и отправленных сообщений
        таблицы статистики пользователей при отправке и принятии сообщений пользователями.

        :param sender: отправитель сообщения.
        :param receiver: получатель сообщения.
        :return: ничего не возвращает.
        """
        sender = self.session.query(self.AllUsers).filter_by(username=sender).first().id
        receiver = self.session.query(self.AllUsers).filter_by(username=receiver).first().id

        sender_instance = self.session.query(self.UsersMessagesHistory).filter_by(user=sender).first()
        sender_instance.sent += 1

        receiver_instance = self.session.query(self.UsersMessagesHistory).filter_by(user=receiver).first()
        receiver_instance.accepted += 1

        self.session.commit()

    def add_contact(self, owner, contact):
        """
        Метод, осуществляющий добавление в БД записи о добавлении пользователя
        другим пользователем в контакты.

        :param owner: пользователь, добавляющий контакт.
        :param contact: пользователь, добавленный в контакты.
        :return: ничего не возвращает.
        """
        owner = self.session.query(self.AllUsers).filter_by(username=owner).first()
        contact = self.session.query(self.AllUsers).filter_by(username=contact).first()

        if not contact or not owner \
                or self.session.query(self.UsersContacts).filter_by(owner=owner.id,
                                                                    contact=contact.id).count():
            return

        instance = self.UsersContacts(owner.id, contact.id)
        self.session.add(instance)
        self.session.commit()

    def remove_contact(self, owner, contact):
        """
        Метод, осуществляющий удаление из БД записи о наличии контакта.

        :param owner: пользователь, удаляющий контакт.
        :param contact: пользователь, удаленный из контактов.
        :return: ничего не возвращает.
        """
        owner = self.session.query(self.AllUsers).filter_by(username=owner).first()
        contact = self.session.query(self.AllUsers).filter_by(username=contact).first()

        if not owner or not contact:
            return

        self.session.query(self.UsersContacts).filter(
            self.UsersContacts.owner == owner.id,
            self.UsersContacts.contact == contact.id,
        ).delete()

        self.session.commit()

    def user_logout(self, username):
        """
        Метод, удаляющий из таблицы пользователей онлайн запись при
        отключения пользователя от сервера.

        :param username: пользователь, отключившийся от сервера
        :return: ничего не возвращает.
        """
        user = self.session.query(self.AllUsers).filter_by(username=username).first()
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
        self.session.commit()

    def get_hash(self, username):
        """
        Метод, возвращающий хеш пароля пользователя.

        :param username: пользователь, чей хеш запрашивается.
        :return: хеш пароля.
        """
        user_instance = self.session.query(self.AllUsers).filter_by(username=username).first()
        return user_instance.password_hash

    def get_pubkey(self, username):
        """
        Метод, возвращающий публичный ключ пользователя.

        :param username: пользователь, чей публичный ключ запрашивается.
        :return: публичный ключ.
        """
        user_instance = self.session.query(self.AllUsers).filter_by(username=username).first()
        return user_instance.pubkey

    def check_user(self, username):
        """
        Метод, осуществляющий проверку регистрации пользователя на сервере.

        :param username: имя пользователя.
        :return: True или False (в зависимости от результата проверки)
        """
        if self.session.query(self.AllUsers).filter_by(username=username).count():
            return True
        else:
            return False

    def get_contacts(self, owner):
        """
        Метод, возвращающий список контактов указанного пользователя.

        :param owner: имя пользователя, чьи контакты запрашиваются.
        :return: список контактов.
        """
        owner = self.session.query(self.AllUsers).filter_by(username=owner).one()

        contacts = self.session.query(self.UsersContacts, self.AllUsers.username).filter_by(owner=owner.id).join(
            self.AllUsers, self.UsersContacts.contact == self.AllUsers.id)

        return [contact[1] for contact in contacts.all()]

    def message_history(self):
        """
        Метод, возвращающий статистику сообщений пользователей.

        :return: список кортежей.
        """
        query = self.session.query(
            self.AllUsers.username,
            self.AllUsers.last_login,
            self.UsersMessagesHistory.sent,
            self.UsersMessagesHistory.accepted,
        ).join(self.AllUsers)
        return query.all()

    def users_list(self):
        """
        Метод, возвращающий список зарегистрированных пользователей.

        :return: список кортежей.
        """
        query = self.session.query(
            self.AllUsers.username,
            self.AllUsers.last_login,
        )
        return query.all()

    def active_users_list(self):
        """
        Метод, возвращающий список пользователей онлайн.

        :return: список кортежей.
        """
        query = self.session.query(
            self.AllUsers.username,
            self.ActiveUsers.address,
            self.ActiveUsers.port,
            self.ActiveUsers.login_time,
        ).join(self.AllUsers)
        return query.all()

    def login_history(self, username=None):
        """
        Метод, возвращающий историю входов (определенного пользователя, если пользователь указан).
        Если пользователь не указан, возвращает статистику всех пользователей.

        :param username: имя пользователя (опционально).
        :return: список кортежей.
        """
        query = self.session.query(
            self.AllUsers.username,
            self.LoginHistory.date,
            self.LoginHistory.address,
            self.LoginHistory.port,
        ).join(self.AllUsers)
        if username:
            query = query.filter(self.AllUsers.username == username)
        return query.all()
