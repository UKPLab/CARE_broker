from broker import init_logging


class Socket:
    """
    Base socket class
    """

    def __init__(self, name, db, socketio):
        self.name = name
        self.db = db
        self.socketio = socketio

        self.logger = init_logging("sockets:{}".format(name))

        self._init()

    def _init(self):
        """
        Initialize the sockets
        :return: True if successful, False otherwise
        """
        pass
