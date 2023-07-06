import json

from flask import session

from broker import init_logging


class Register:
    """
    Basic socket.io event handlers for skill and task management

    @author: Dennis Zyska, Nils Dycke
    """

    def __init__(self, socketio, skills, tasks, clients):
        self.socketio = socketio
        self.tasks = tasks
        self.skills = skills
        self.clients = clients
        self.logger = init_logging("register")

        self._init()

    def _init(self):
        self.socketio.on_event("skillRegister", self.register)
        self.socketio.on_event("skillGetAll", self.get_all)
        self.socketio.on_event("skillGetConfig", self.get_config)
        self.socketio.on_event("skillRequest", self.request)
        self.socketio.on_event("taskResults", self.results)

    def register(self, data):
        """
        Registers a skill on the broker.

        :param data: Data Object
        """
        try:
            if isinstance(data, str):  # needed for c++ socket.io client
                data = json.loads(data)

            if self.clients.check_quota(session["sid"], append=True):
                return

            self.skills.register(session["sid"], data)
        except:
            self.logger.error("Error in request {}: {}".format("skillRegister", data))
            self.socketio.emit("requestError", {"message": "Error in request!"}, to=session["sid"])


    def get_all(self):
        """
        Informs the client about all skills currently registered on the broker.

        This should be called after a client connects to the broker. Further updates are provided by the
        "skillRegister" event.
        """
        try:
            if self.clients.check_quota(session["sid"], append=True):
                return

            self.skills.send_update(to=session["sid"])
        except:
            self.logger.error("Error in request {}".format("skillGetAll"))
            self.socketio.emit("requestError", {"message": "Error in request!"}, to=session["sid"])


    def get_config(self, data):
        """
        Get configuration from a skill by name
        """
        try:
            if self.clients.check_quota(session["sid"], append=True):
                return

            self.skills.send_update(data['name'], with_config=True, to=session["sid"])
        except:
            self.logger.error("Error in request {}: {}".format("skillGetConfig", data))
            self.socketio.emit("requestError", {"message": "Error in request!"}, to=session["sid"])


    def request(self, data):
        """
        Request a specific skill by name
        """
        try:
            if self.clients.check_quota(session["sid"], append=True):
                return

            # get all available nodes for skill; get a random owner from the list
            node = self.skills.get_node(data["name"])
            if node is None:
                self.socketio.emit("requestError", {"message": "No node for this skill available!"}, to=session["sid"])
            else:
                # cache requests
                task = self.tasks.create(session["sid"], node, data)
                # request skill of the owner
                self.socketio.emit("taskRequest", {'id': task['_key'], 'data': data['data']}, room=node)
        except:
            self.logger.error("Error in request {}: {}".format("skillRequest", data))
            self.socketio.emit("requestError", {"message": "Error in request!"}, to=session["sid"])

    def results(self, data):
        """
        Send results to client
        """
        try:
            node = session["sid"]
            if self.clients.check_quota(node, append=True, results=True):
                return

            if type(data) is dict and "id" in data and "data" in data:
                self.tasks.finish(data["id"], node, data)
        except:
            self.logger.error("Error in request {}: {}".format("taskResults", data))
            self.socketio.emit("requestError", {"message": "Error in request!"}, to=session["sid"])

