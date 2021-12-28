from datetime import datetime

from sqlalchemy import (Column, DateTime, Integer, MetaData, String, Table,
                        Text, create_engine)
from sqlalchemy.orm import mapper, sessionmaker
from sqlalchemy.sql import default_comparator


class ClientDatabase:
    """
    Класс-оболочка для работы с базой данных клиента.
    Использует SQLite базу данных, реализован с помощью
    SQLAlchemy ORM и используется классический подход.
    """

    class KnownUsers:
        """
        Класс-отображения таблицы пользователей.
        """

        def __init__(self, username):
            self.id = None
            self.username = username

    class UserMessagesHistory:
        """
        Класс-отображение таблицы статистики сообщений.
        """

        def __init__(self, sender, receiver, message):
            self.id = None
            self.sender = sender
            self.receiver = receiver
            self.message = message
            self.date = datetime.now()

    class UserContacts:
        """
        Класс-отображение таблицы контактов.
        """

        def __init__(self, contact):
            self.id = None
            self.contact = contact

    def __init__(self, username):
        self.database_engine = create_engine(f'sqlite:///client/client/{username}.db3', echo=False, pool_recycle=3600,
                                             connect_args={'check_same_thread': False})

        self.metadata = MetaData()

        known_users_table = Table('KnownUsers', self.metadata,
                                  Column('id', Integer, primary_key=True),
                                  Column('username', String),
                                  )

        messages_history_table = Table('MessagesHistory', self.metadata,
                                       Column('id', Integer, primary_key=True),
                                       Column('sender', String),
                                       Column('receiver', String),
                                       Column('message', Text),
                                       Column('date', DateTime),
                                       )

        user_contacts_table = Table('Contacts', self.metadata,
                                    Column('id', Integer, primary_key=True),
                                    Column('contact', String, unique=True),
                                    )

        self.metadata.create_all(self.database_engine)

        mapper(self.KnownUsers, known_users_table)
        mapper(self.UserMessagesHistory, messages_history_table)
        mapper(self.UserContacts, user_contacts_table)

        session = sessionmaker(bind=self.database_engine)
        self.session = session()

        self.session.query(self.UserContacts).delete()
        self.session.commit()

    def init_active_users(self, users_list):
        """
        Метод, заполняющий таблицу известных пользователей.

        :param users_list: список известных пользователей, полученный с сервера.
        :return: ничего не возвращает.
        """
        self.session.query(self.KnownUsers).delete()
        for user in users_list:
            user_instance = self.KnownUsers(user)
            self.session.add(user_instance)
        self.session.commit()

    def get_active_users(self):
        """
        Метод, возвращающий список всех известных пользователей.

        :return: список всех известных пользователей.
        """
        return [user[0] for user in self.session.query(self.KnownUsers.username).all()]

    def check_user_in_active(self, username):
        """
        Метод, проверяющий существование пользователя.

        :param username: пользователь, проверяющийся на существование.
        :return: True или False (в зависимости от результат).
        """
        if self.session.query(self.KnownUsers).filter_by(username=username).count():
            return True
        else:
            return False

    def add_contact(self, contact):
        """
        Метод, добавляющий контакт в базу данных.

        :param contact: пользователь, которого необходимо добавить в контакты.
        :return: ничего не возвращает.
        """
        if not self.session.query(self.UserContacts).filter_by(contact=contact).count():
            contact_instance = self.UserContacts(contact)
            self.session.add(contact_instance)
            self.session.commit()

    def delete_contact(self, contact):
        """
        Метод, удаляющий контакт из базы данных.

        :param contact: пользователь, которого необходимо удалить из контактов.
        :return: ничего не возвращает.
        """
        self.session.query(self.UserContacts).filter_by(contact=contact).delete()
        self.session.commit()

    def get_user_contacts(self):
        """
        Метод, возвращающий список всех контактов пользователя.

        :return: список пользователей контакта.
        """
        return [contact[0] for contact in self.session.query(self.UserContacts.contact).all()]

    def check_user_contact(self, username):
        """
        Метод, проверяющий наличие пользователя в таблице контактов.

        :param username: пользователь, искомый в списке контактов.
        :return: True или False (в зависимости от результат).
        """
        if self.session.query(self.UserContacts).filter_by(contact=username).count():
            return True
        else:
            return False

    def save_user_message(self, sender, receiver, message):
        """
        Метод, сохраняющий сообщение в базу данных.

        :param sender: отправитель сообщения.
        :param receiver: получатель сообщения.
        :param message: сообщение.
        :return: ничего не возвращает.
        """
        message_instance = self.UserMessagesHistory(sender, receiver, message)
        self.session.add(message_instance)
        self.session.commit()

    def get_user_messages_history(self, sender=None, receiver=None):
        """
        Метод, возвращающий историю сообщений в соответствии с заданными параметрами.

        :param sender: отправитель сообщения.
        :param receiver: получатель сообщения.
        :return: список сообщений.
        """
        query = self.session.query(self.UserMessagesHistory)
        if sender:
            query = query.filter_by(sender=sender)
        if receiver:
            query = query.filter_by(receiver=receiver)
        return [(row.sender, row.receiver, row.message, row.date) for row in query.all()]


if __name__ == '__main__':
    test_db = ClientDatabase('test1')

    test_db.init_active_users(['test2', 'test3', 'test4'])
    print(test_db.get_active_users())

    print(test_db.check_user_in_active('test2'))
    print(test_db.check_user_in_active('test5'))

    print(test_db.get_user_contacts())
    test_db.add_contact('test3')
    print(test_db.check_user_contact('test3'))
    print(test_db.get_user_contacts())

    test_db.add_contact('test4')
    print(test_db.check_user_contact('test4'))
    print(test_db.get_user_contacts())

    test_db.delete_contact('test4')
    print(test_db.check_user_contact('test4'))
    print(test_db.get_user_contacts())

    # test_db.save_user_message('test1', 'test2', 'Test message №1')
    # test_db.save_user_message('test2', 'test1', 'Test message №2')
    print(test_db.get_user_messages_history())
    print(test_db.get_user_messages_history(sender='test1'))
    print(test_db.get_user_messages_history(receiver='test1'))
