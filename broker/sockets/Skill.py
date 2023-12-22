import json

from flask import session

from broker.sockets import Socket


class Skill(Socket):
    """
    Basic socket.io event handlers for authentication

    @author: Dennis Zyska
    """

    def __init__(self, db, socketio):
        super().__init__("skill", db, socketio)

    def _init(self):
        self.socketio.on_event("skillRegister", self.register)
        self.socketio.on_event("skillGetAll", self.get_all)
        self.socketio.on_event("skillGetConfig", self.get_config)

    def get_config(self, data):
        """
        Get configuration from a skill by name
        """
        try:
            if self.db.clients.quota(session["sid"], append=True):
                self.socketio.emit("error", {"code": 100}, to=session["sid"])
                return

            client = self.db.clients.get(session["sid"])
            skills = self.db.skills.get_skills(filter_role=client["role"], filter_name=data["name"], with_config=True)

            if len(skills) == 0:
                self.socketio.emit("error", {"code": 203}, to=session["sid"])
                return

            self.socketio.emit("skillConfig", skills[0]['config'], to=session["sid"])
        except Exception as e:
            self.logger.error("Error in request {}: {}".format("skillGetConfig", data))
            self.logger.error(e)
            self.socketio.emit("error", {"code": 500}, to=session["sid"])

    def get_all(self):
        """
        Informs the client about all skills currently registered on the broker.

        This should be called after a client connects to the broker. Further updates are provided by the
        "skillRegister" event.
        """
        try:
            if self.db.clients.quota(session["sid"], append=True):
                self.socketio.emit("error", {"code": 100}, to=session["sid"])
                return

            client = self.db.clients.get(session["sid"])

            self.db.skills.send_all(role=client['role'], to=session["sid"])
        except Exception as e:
            self.logger.error("Error in request {}".format("skillGetAll"))
            self.logger.error(e)
            self.socketio.emit("error", {"code": 500}, to=session["sid"])

    def register(self, data):
        """
        Registers a skill on the broker.

        :param data: Data Object
        """
        try:
            if isinstance(data, str):  # needed for c++ socket.io client
                data = json.loads(data)

            if self.db.clients.quota(session["sid"], append=True):
                return

            if 'name' in data:
                self.db.skills.register(session["sid"], data)
            else:
                self.socketio.emit("error", {"code": 202}, to=session["sid"])
        except Exception as e:
            self.logger.error("Error in request {}: {}".format("skillRegister", data))
            self.logger.error(e)
            self.socketio.emit("error", {"code": 500}, to=session["sid"])
