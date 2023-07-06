import os
from datetime import datetime

from flask_socketio import join_room

from broker import init_logging
from broker.db import results
from broker.utils.Quota import Quota


class Clients:
    """
    Representation of a client in the broker (through db)

    @author: Dennis Zyska
    """

    def __init__(self, db, socketio):
        self.socketio = socketio
        self.quota = Quota(max_len=int(os.getenv("QUOTA_CLIENTS", 20)) + 1)
        self.quota_results = Quota(max_len=int(os.getenv("QUOTA_RESULTS", 100)) + 1)
        self.logger = init_logging("clients")

        if results(db.has_collection("clients")):
            self.db = db.collection("clients")
        else:
            self.db = results(db.create_collection("clients"))
        self.index = results(self.db.add_hash_index(fields=['sid'], name='sid_index', unique=False))

        self.clean()

    def connect(self, sid, ip, data):
        """
        Connect a client
        :param sid: session id
        :param ip: ip address
        :param data: payload
        :return:
        """
        join_room(sid)
        return self.db.insert(
            {
                "sid": sid,
                "ip": ip,
                "data": data,
                "connected": True,
                "first_contact": datetime.now().isoformat(),
                "last_contact": datetime.now().isoformat(),
                "reconnects": 1,
            }
        )

    def disconnect(self, sid):
        self.db.update_match({"sid": sid, "connected": True},
                             {'last_contact': datetime.now().isoformat(), 'connected': False})

        # delete quota for sid
        self.quota.delete(sid)
        self.quota_results.delete(sid)

        self.socketio.close_room(sid)

    def check_quota(self, sid, append=False, results=False):
        """
        Check if a client is allowed to send data
        :param results: use results quota
        :param sid: session id
        :param append: append to quota
        :return: True if quota is exceeded
        """
        self.db.update_match({"sid": sid, "connected": True}, {'last_contact': datetime.now().isoformat()})
        if results:
            return self.quota_results(sid, append)
        return self.quota(sid, append)

    def clean(self):
        """
        Clean up old clients and reset quota
        """
        cleaned = results(self.db.update_match({"connected": True}, {"connected": False, "cleaned": True}))
        self.logger.info("Cleaned up {} clients".format(cleaned))
        self.quota.reset()
        self.quota_results.reset()
