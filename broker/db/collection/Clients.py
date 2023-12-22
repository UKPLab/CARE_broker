from datetime import datetime

from flask_socketio import join_room

from broker.db.utils import results
from broker.db.collection import Collection
from broker.utils.JobQuota import JobQuota
from broker.utils.Quota import Quota


class Clients(Collection):
    """
    Client Collection

    @author: Dennis Zyska
    """

    def __init__(self, db, adb, config, socketio):
        super().__init__("clients", db, adb, config, socketio)
        self.quotas = {}
        self.index = results(self.collection.add_hash_index(fields=['sid'], name='sid_index', unique=False))
        self.index = results(self.collection.add_hash_index(fields=['connected'], name='connected_index', unique=False))

    def connect(self, sid, ip, data, default_role="guest"):
        """
        Connect a client
        :param sid: session id
        :param ip: ip address
        :param data: payload
        :param default_role: basic role
        :return:
        """
        role = self.db.roles.get(default_role)
        user = results(self.collection.insert(
            {
                "sid": sid,
                "ip": ip,
                "data": data,
                "role": role['name'],
                "connected": True,
                "first_contact": datetime.now().isoformat(),
                "last_contact": datetime.now().isoformat(),
            }
        ))
        join_room(sid)
        join_room(role['room'])

        # add quota for sid
        self._apply_quota(sid, role['name'])

        # send skills
        self.db.skills.send_all(role['name'], to=sid)

        return user

    def disconnect(self, sid):
        self.collection.update_match({"sid": sid, "connected": True},
                             {'last_contact': datetime.now().isoformat(), 'connected': False})

        # remove sid from quota
        del self.quotas[sid]

        # close room
        self.socketio.close_room(sid)

        # cancel jobs
        self.db.tasks.terminate_by_disconnect(sid=sid)

        # remove skills by sid if exists
        self.db.skills.unregister(sid=sid)


    def _apply_quota(self, sid, role):
        """
        Set quota for client
        :param sid: session id
        :param role: name of the role
        :return:
        """
        if sid in self.quotas:
            del self.quotas[sid]

        # set quota interval if set
        quotaInterval = 1
        if 'quotaInterval' in self.config:
            quotaInterval = self.config['quotaInterval']

        role = self.db.roles(role)
        self.quotas[sid] = {
            "role": role,
            "requests": Quota(max_len=role['quota']['requests'], interval=quotaInterval),
            "results": Quota(max_len=role['quota']['results'], interval=quotaInterval),
            "jobs": JobQuota(max_len=role['quota']['jobs']),
        }

    def get(self, sid):
        """
        Get client by sid
        :param sid: session id
        :return:
        """
        client = results(self.collection.find({"sid": sid, "connected": True}))
        if client.count() > 0:
            return client.next()

    def register(self, sid, secret):
        """
        Try to register a client with a public key
        :param secret: secret string
        :param sid: session id
        :return:
        """
        self.collection.update_match({"sid": sid, "connected": True},
                             {'last_contact': datetime.now().isoformat(), 'secret': secret})

    def save(self, client):
        """
        Save a client object
        :param client: client object
        :return:
        """
        # update quota if role changed
        if "role" in client:
            if self.quotas[client["sid"]]["role"] != client["role"]:
                self._apply_quota(client["sid"], client["role"])

        self.collection.update(client)

    def quota(self, sid, append=False, is_result=False, is_job=False):
        """
        Check if a client is allowed to send data
        :param is_result: use results quota
        :param is_job: use job quota
        :param sid: session id
        :param append: append to quota
        :return: True if quota is exceeded
        """
        self.collection.update_match({"sid": sid, "connected": True}, {'last_contact': datetime.now().isoformat()})
        if is_result:
            return self.quotas[sid]['results'](append)
        elif is_job:
            return self.quotas[sid]['jobs'](append)
        return self.quotas[sid]['requests'](append)

    def clean(self):
        """
        Clean up old clients and reset quota
        """
        cleaned = results(self.collection.update_match({"connected": True}, {"connected": False, "cleaned": True}))
        self.logger.info("Cleaned up {} clients".format(cleaned))
