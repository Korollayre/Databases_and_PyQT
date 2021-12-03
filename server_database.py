from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, DateTime
from sqlalchemy.orm import mapper, sessionmaker

from datetime import datetime
from tabulate import tabulate


class ServerDatabase:
    class AllUsers:
        def __init__(self, username):
            self.id = None
            self.username = username
            self.last_login = datetime.now()

    class ActiveUsers:
        def __init__(self, user_id, address, port, login_time):
            self.id = None
            self.user = user_id
            self.address = address
            self.port: int = port
            self.login_time = login_time

    class LoginHistory:
        def __init__(self, user, date, address, port):
            self.id = None
            self.user = user
            self.date = date
            self.address = address
            self.port: int = port

    class UsersContacts:
        def __init__(self, owner, contact):
            self.id = None
            self.owner = owner
            self.contact = contact

    class UsersMessagesHistory:
        def __init__(self, user):
            self.id = None
            self.user = user
            self.sent: int = 0
            self.accepted: int = 0

    def __init__(self, path):
        self.database_engine = create_engine(f'sqlite:///{path}', echo=False, pool_recycle=3600,
                                             connect_args={'check_same_thread': False})

        self.metadata = MetaData()

        users_table = Table('Users', self.metadata,
                            Column('id', Integer, primary_key=True),
                            Column('username', String, unique=True),
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

    def user_login(self, username, address, port):

        query = self.session.query(self.AllUsers).filter_by(username=username)

        if query.count():
            user = query.first()
            user.last_login = datetime.now()
        else:
            user = self.AllUsers(username)
            self.session.add(user)
            self.session.commit()
            user_message_history = self.UsersMessagesHistory(user.id)
            self.session.add(user_message_history)

        new_active_user = self.ActiveUsers(user.id, address, port, datetime.now())
        self.session.add(new_active_user)

        user_history = self.LoginHistory(user.id, datetime.now(), address, port)
        self.session.add(user_history)

        self.session.commit()

    def message_exchange(self, sender, receiver):
        sender = self.session.query(self.AllUsers).filter_by(username=sender).first().id
        receiver = self.session.query(self.AllUsers).filter_by(username=receiver).first().id

        sender_instance = self.session.query(self.UsersMessagesHistory).filter_by(user=sender).first()
        sender_instance.sent += 1

        receiver_instance = self.session.query(self.UsersMessagesHistory).filter_by(user=receiver).first()
        receiver_instance.accepted += 1

        self.session.commit()

    def add_contact(self, owner, contact):
        owner = self.session.query(self.AllUsers).filter_by(username=owner).first()
        contact = self.session.query(self.AllUsers).filter_by(username=contact).first()

        if not contact or not owner or self.session.query(self.UsersContacts).filter_by(owner=owner.id,
                                                                                        contact=contact.id).count():
            return

        instance = self.UsersContacts(owner.id, contact.id)
        self.session.add(instance)
        self.session.commit()

    def remove_contact(self, owner, contact):
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

        user = self.session.query(self.AllUsers).filter_by(username=username).first()
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
        self.session.commit()

    def get_contacts(self, owner):
        owner = self.session.query(self.AllUsers).filter_by(username=owner).one()

        contacts = self.session.query(self.UsersContacts, self.AllUsers.username).filter_by(owner=owner.id).join(
            self.AllUsers, self.UsersContacts.contact == self.AllUsers.id)

        return [contact[1] for contact in contacts.all()]

    def message_history(self, username=None):
        query = self.session.query(
            self.AllUsers.username,
            self.AllUsers.last_login,
            self.UsersMessagesHistory.sent,
            self.UsersMessagesHistory.accepted,
        ).join(self.AllUsers)
        if username:
            query = query.filter(self.AllUsers.username == username)
        return query.all()

    def users_list(self):
        query = self.session.query(
            self.AllUsers.username,
            self.AllUsers.last_login,
        )
        return query.all()

    def active_users_list(self):
        query = self.session.query(
            self.AllUsers.username,
            self.ActiveUsers.address,
            self.ActiveUsers.port,
            self.ActiveUsers.login_time,
        ).join(self.AllUsers)
        return query.all()

    def login_history(self, username=None):
        query = self.session.query(
            self.AllUsers.username,
            self.LoginHistory.date,
            self.LoginHistory.address,
            self.LoginHistory.port,
        ).join(self.AllUsers)
        if username:
            query = query.filter(self.AllUsers.username == username)
        return query.all()


if __name__ == '__main__':
    test_db = ServerDatabase()
    test_db.user_login('client_1', '192.168.0.10', 8888)
    test_db.user_login('client_2', '192.168.0.11', 7777)
    test_db.user_login('client_3', '192.168.0.11', 8888)

    print(tabulate(test_db.active_users_list()))

    test_db.message_exchange('client_1', 'client_3')
    test_db.message_exchange('client_3', 'client_1')
    test_db.message_exchange('client_2', 'client_1')

    print(tabulate(test_db.message_history('client_1')))
    print(tabulate(test_db.message_history('client_2')))

    test_db.add_contact('client_1', 'client_2')
    test_db.add_contact('client_1', 'client_3')

    print(tabulate(test_db.get_contacts('client_1')))

    test_db.remove_contact('client_1', 'client_3')

    print(tabulate(test_db.get_contacts('client_1')))
    # test_db.user_logout('client_1')
    # print(test_db.active_users_list())
    # print(test_db.login_history('client_1'))
    #
    # test_db.user_logout('client_2')
    # print(test_db.active_users_list())
    # print(test_db.users_list())
