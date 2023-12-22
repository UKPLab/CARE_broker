import os

from Crypto.Hash import SHA256
from flask import request, session
from flask_socketio import join_room, leave_room

from broker.sockets import Socket
from broker.utils.Keys import verify


class Auth(Socket):
    """
    Basic socket.io event handlers for authentication

    @author: Dennis Zyska
    """

    def __init__(self, db, socketio):
        super().__init__("skill", db, socketio)

    def _init(self):
        self.socketio.on_event("authRequest", self.request)
        self.socketio.on_event("authResponse", self.response)
        self.socketio.on_event("authStatus", self.status)

    def response(self, data):
        """
        Register as a client, receive public key and associate with user
        :param data: object with public key and signature {pub:...,sig:...}
        :return:
        """
        try:
            if self.db.clients.quota(session["sid"], append=True):
                self.socketio.emit("error", {"code": 100}, to=session["sid"])
                return
            client = self.db.clients.get(session["sid"])
            if "secret" in client:
                if verify(client['secret'], data['sig'], data['pub']):
                    user = self.db.users.auth(session["sid"], data['pub'])
                    user = self.db.users.get(user['_key'])
                    client['user'] = user['_key']

                    # updating client role
                    client['role'] = user['role']
                    leave_room("role:guests")
                    join_room("role:{}".format(user['role']))

                    # send skill updates as role changed
                    self.db.skills.send_all(role=user['role'], to=session["sid"])

                    self.db.clients.save(client)
                    self.status()
                else:
                    self.logger.error("Error in verify {}: {}".format(session["sid"], data))
                    self.socketio.emit("error", {"code": 401}, to=session["sid"])
            else:
                self.request()
        except Exception as e:
            self.logger.error("Error in request {}: {}".format("authRegister", data))
            self.logger.error(e)
            self.socketio.emit("error", {"code": 500}, to=session["sid"])

    def request(self, data=None):
        """
        Authenticate a user, assign client to user
        :param data: object with public and signature
        :return:
        """
        try:
            if self.db.clients.quota(session["sid"], append=True):
                self.socketio.emit("error", {"code": 100}, to=session["sid"])
                return
            # create secret message to sign by client
            secret_message = "{}{}".format(request.sid, os.getenv("SECRET", "astringency"))
            hash = SHA256.new()
            hash.update(secret_message.encode("utf8"))
            self.db.clients.register(request.sid, hash.hexdigest())
            self.socketio.emit("authChallenge", {"secret": hash.hexdigest()})
        except Exception as e:
            self.logger.error("Error in request {}".format("authRequest"))
            self.logger.error(e)
            self.socketio.emit("error", {"code": 500}, to=session["sid"])

    def status(self):
        """
        Send current authentication status
        :return:
        """
        try:
            if self.db.clients.quota(session["sid"], append=True):
                self.socketio.emit("error", {"code": 100}, to=session["sid"])
                return
            client = self.db.clients.get(session["sid"])
            if "user" in client:
                user = self.db.users.get(client['user'])
                if user:
                    self.socketio.emit("authInfo", {"role": user['role']}, to=session["sid"])
                else:
                    self.socketio.emit("authInfo", {"role": "guest"}, to=session["sid"])
            else:
                self.socketio.emit("authInfo", {"role": "guest"}, to=session["sid"])
        except Exception as e:
            self.logger.error("Error in request {}.".format("authStatus"))
            self.logger.error(e)
            self.socketio.emit("error", {"code": 500}, to=session["sid"])
