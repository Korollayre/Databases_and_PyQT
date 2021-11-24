from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, DateTime
from sqlalchemy.orm import mapper, sessionmaker

from datetime import datetime


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
            self.port = port
            self.login_time = login_time

    class LoginHistory:
        def __init__(self, username, date, address, port):
            self.id = None
            self.username = username
            self.date = date
            self.address = address
            self.port = port

    def __init__(self):
        self.database_engine = create_engine('sqlite:///server_base.db3', echo=False, pool_recycle=3600)
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
                                  Column('username', ForeignKey('Users.id')),
                                  Column('date', DateTime),
                                  Column('address', String),
                                  Column('port', Integer),
                                  )

        self.metadata.create_all(self.database_engine)

        mapper(self.AllUsers, users_table)
        mapper(self.ActiveUsers, active_users_table)
        mapper(self.LoginHistory, users_login_table)

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

        new_active_user = self.ActiveUsers(user.id, address, port, datetime.now())
        self.session.add(new_active_user)

        user_history = self.LoginHistory(user.id, datetime.now(), address, port)
        self.session.add(user_history)

        self.session.commit()

    def user_logout(self, username):

        user = self.session.query(self.AllUsers).filter_by(username=username).first()
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
        self.session.commit()

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

    print(test_db.active_users_list())

    test_db.user_logout('client_1')
    print(test_db.active_users_list())
    print(test_db.login_history('client_1'))

    test_db.user_logout('client_2')
    print(test_db.active_users_list())
    print(test_db.users_list())
