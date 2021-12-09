from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, DateTime, Text
from sqlalchemy.orm import mapper, sessionmaker

from datetime import datetime


class ClientDatabase:
    class KnownUsers:
        def __init__(self, username):
            self.id = None
            self.username = username

    class UserMessagesHistory:
        def __init__(self, sender, receiver, message):
            self.id = None
            self.sender = sender
            self.receiver = receiver
            self.message = message
            self.date = datetime.now()

    class UserContacts:
        def __init__(self, contact):
            self.id = None
            self.contact = contact

    def __init__(self, username):
        self.database_engine = create_engine(f'sqlite:///client/{username}.db3', echo=False, pool_recycle=3600,
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
        self.session.query(self.KnownUsers).delete()
        for user in users_list:
            user_instance = self.KnownUsers(user)
            self.session.add(user_instance)
        self.session.commit()

    def get_active_users(self):
        return [user[0] for user in self.session.query(self.KnownUsers.username).all()]

    def check_user_in_active(self, username):
        if self.session.query(self.KnownUsers).filter_by(username=username).count():
            return True
        else:
            return False

    def add_contact(self, contact):
        if not self.session.query(self.UserContacts).filter_by(contact=contact).count():
            contact_instance = self.UserContacts(contact)
            self.session.add(contact_instance)
            self.session.commit()

    def delete_contact(self, contact):
        self.session.query(self.UserContacts).filter_by(contact=contact).delete()
        self.session.commit()

    def get_user_contacts(self):
        return [contact[0] for contact in self.session.query(self.UserContacts.contact).all()]

    def check_user_contact(self, username):
        if self.session.query(self.UserContacts).filter_by(contact=username).count():
            return True
        else:
            return False

    def save_user_message(self, sender, receiver, message):
        message_instance = self.UserMessagesHistory(sender, receiver, message)
        self.session.add(message_instance)
        self.session.commit()

    def get_user_messages_history(self, sender=None, receiver=None):
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
