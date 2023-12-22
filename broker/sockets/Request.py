import numpy as np
from flask import session

from broker.sockets import Socket


class Request(Socket):
    """
    Basic socket.io event handlers for authentication

    @author: Dennis Zyska
    """

    def __init__(self, db, socketio):
        super().__init__("skill", db, socketio)

    def _init(self):
        self.socketio.on_event("skillRequest", self.request)
        self.socketio.on_event("taskResults", self.results)
        self.socketio.on_event("taskUpdate", self.results)
        self.socketio.on_event("requestAbort", self.abort)

    def request(self, data):
        """
        Request a specific skill by name
        """
        try:
            if self.db.clients.quota(session["sid"], append=True):
                self.socketio.emit("error", {"id": data['id'] if 'id' in data else None, "code": 100},
                                   to=session["sid"])
                return

            # get a node that provides this skill
            node = self.db.skills.get_node(session["sid"], data["name"])
            if node is None:
                self.socketio.emit("error", {"id": data['id'] if 'id' in data else None, "code": 200},
                                   to=session["sid"])
            else:
                # check if the client has enough quota to run this job
                reserve_quota = np.random.randint(1000000, 2 ** 31 - 1)
                if self.db.clients.quota(session["sid"], append=reserve_quota, is_job=True):
                    self.socketio.emit("error", {"id": data['id'] if 'id' in data else None, "code": 101},
                                       to=session["sid"])
                    return

                task_id = self.db.tasks.create(session["sid"], node, data)

                if task_id > 0:
                    self.socketio.emit("taskRequest", {'id': task_id, 'name': data['name'], 'data': data['data']},
                                       room=node['sid'])

                self.db.clients.quotas[session["sid"]]["jobs"].update(reserve_quota, task_id)
        except Exception as e:
            self.logger.error("Error in request {}: {}".format("skillRequest", data))
            self.logger.error(e)
            self.socketio.emit("error", {"code": 500}, to=session["sid"])

    def results(self, data):
        """
        Send results to client
        """
        try:
            node = session["sid"]
            if self.db.clients.quota(node, append=True, is_result=True):
                self.socketio.emit("error", {"code": 100}, to=session["sid"])
                return

            if type(data) is dict and "id" in data and ("error" in data or "data" in data):
                self.db.tasks.update(data["id"], node, data)
            else:
                self.socketio.emit("error", {"code": 111}, to=session["sid"])
                return
        except Exception as e:
            self.logger.error("Error in request {}: {}".format("taskResults", data))
            self.logger.error(e)
            self.socketio.emit("error", {"code": 500}, to=session["sid"])

    def abort(self, data):
        """
        Send results to client
        """
        aborted = self.db.tasks.abort_by_user(data["id"], session["sid"])

        try:
            if self.db.clients.quota(session["sid"], append=True):
                self.socketio.emit("error", {"code": 100}, to=session["sid"])
                return

            aborted = self.db.tasks.abort_by_user(data["id"], session["sid"])
            if not aborted:
                self.socketio.emit("error", {"code": 106}, to=session["sid"])
        except Exception as e:
            self.logger.error("Error in request {}: {}".format("requestAbort", data))
            self.logger.error(e)
            self.socketio.emit("error", {"code": 500}, to=session["sid"])
