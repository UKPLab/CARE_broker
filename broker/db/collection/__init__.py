import threading

from broker import init_logging
from broker.db.utils import results


class Collection:
    """
    Representation of the database in the broker
    """

    def __init__(self, name, db, adb, config, socketio):
        self.name = name
        self._sysdb = adb
        self.config = config
        self.db = db
        self.socketio = socketio
        self.logger = init_logging("collection:{}".format(name))

        self._init()
        if 'cleanDbOnStart' in self.config and self.config['cleanDbOnStart']:
            self.clean()

    def _init(self):
        """
        Initialize the database
        :return: True if successful, False otherwise
        """
        if results(self._sysdb.has_collection(self.name)):
            self.collection = self._sysdb.collection(self.name)
        else:
            self.collection = results(self._sysdb.create_collection(self.name))

        # start scrub task
        scrub_thread = threading.Thread(target=self.scrub)
        scrub_thread.daemon = True
        scrub_thread.start()

        return True

    def get(self, key):
        """
        Get entry by db key
        :param key: database key of entry
        :return:
        """
        return results(self.collection.get("{}".format(key)))

    def clean(self):
        """
        Clean the database
        :return: True if successful, False otherwise
        """
        pass

    def scrub(self):
        """
        Scrub the database
        :return: True if successful, False otherwise
        """
        pass
