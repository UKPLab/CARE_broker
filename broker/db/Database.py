import os

from arango import ArangoClient

from broker.db.collection.Clients import Clients
from broker.db.collection.Roles import Roles
from broker.db.collection.Skills import Skills
from broker.db.collection.Tasks import Tasks
from broker.db.collection.Users import Users


class Database:
    """
    Holds the database connection
    """

    def __init__(self, url=None, username="root", password=None, db_name="broker", config=None, socketio=None):
        if url:
            self.url = url
        else:
            url = "http://{}:{}".format(os.getenv("ARANGODB_HOST", "localhost"), os.getenv("ARANGODB_PORT", "8529"))
        self._username = username
        self._password = password if password else os.getenv("ARANGODB_ROOT_PASSWORD", "root")
        self.db_name = db_name

        self.async_db, self.sync_db, self.sys_db = self._connect()
        self.async_db.clear_async_jobs()
        self.db = self.async_db  # make async_db the default db

        # initialize collections
        self.clients = Clients(db=self, adb=self.async_db, config=config, socketio=socketio)
        self.tasks = Tasks(db=self, adb=self.async_db, config=config, socketio=socketio)
        self.skills = Skills(db=self, adb=self.async_db, config=config, socketio=socketio)
        self.users = Users(db=self, adb=self.async_db, config=config, socketio=socketio)
        self.roles = Roles(db=self, adb=self.async_db, config=config, socketio=socketio)

    def _connect(self):
        """
        Connects to arangodb
        :return: db instance
        """
        db_client = ArangoClient(hosts=self.url)
        sys_db = db_client.db('_system', username=self._username, password=self._password)
        if not sys_db.has_database(self.db_name):
            sys_db.create_database(self.db_name)
        sync_db = db_client.db(self.db_name, username='root', password=self._password)
        async_db = sync_db.begin_async_execution(return_result=True)
        return async_db, sync_db, sys_db
