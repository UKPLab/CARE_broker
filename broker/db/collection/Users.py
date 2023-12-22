from datetime import datetime

from broker.db.utils import results
from broker.db.collection import Collection
from broker.utils.Keys import Keys

from arango.exceptions import DocumentRevisionError

class Users(Collection):
    """
    Users Collection

    @author: Dennis Zyska
    """

    def __init__(self, db, adb, config, socketio):
        super().__init__("users", db, adb, config, socketio)
        self.quotas = {}

        self.index = results(self.collection.add_hash_index(fields=['sid'], name='sid_index', unique=False))
        self.index = results(self.collection.add_hash_index(fields=['connected'], name='connected_index', unique=False))

    def reinit(self, private_key_path = "./private_key.pem"):
        """
        Reinitialize the collection
        :param private_key_path: path to private key
        :return:
        """
        self._init(reinit=True, private_key_path=private_key_path)

    def _init(self, reinit=False, private_key_path="./private_key.pem"):
        """
        Check if necessary keys exists, if not create
        :param reinit: overwrite basic clients
        :param private_key_path: path to private key
        :return:
        """
        super()._init()

        basic_client = results(self.collection.find({"system": True}))
        if reinit or basic_client.count() == 0:

            # load keys
            keys = Keys(private_key_path=private_key_path)
            if basic_client.count() > 0:
                for c in basic_client:
                    if basic_client.has_more():
                        self.collection.delete(c)

                c['key'] = keys.get_public()
                c['updated'] = datetime.now().isoformat()

                results(self.collection.update(c))

            else:
                # generate key pair
                results(self.collection.insert(
                    {
                        "system": True,
                        "role": "admin",
                        "authenticated": 0,
                        "key": keys.get_public(),
                        "created": datetime.now().isoformat(),
                        "updated": datetime.now().isoformat()
                    }
                ))

    def set_role(self, public, role):
        """
        Set a role to user
        :param public: public key
        :param role: role name
        :return:
        """
        client = results(self.collection.find({"key": public}, limit=1))
        if client.count() > 0:
            c = client.next()
            c['role'] = role
            c["updated"]: datetime.now().isoformat()
            return results(self.collection.update(c))
        return False

    def auth(self, sid, public):
        """
        Register user
        :param sid: session id
        :param data: public key and additional infos
        :return:
        """
        client = results(self.collection.find({"key": public}, limit=1))
        if client.count() > 0:
            c = client.next()
            c['authenticated'] = c['authenticated'] + 1
            c["updated"]: datetime.now().isoformat()
            try:
                return results(self.collection.update(c))
            except DocumentRevisionError as e:
                self.logger.error(e)
                return results(self.collection.get(c['key']))
        else:
            return results(self.collection.insert(
                {
                    "role": "user",
                    "key": public,
                    "authenticated": 1,
                    "created": datetime.now().isoformat(),
                    "updated": datetime.now().isoformat()
                }
            ))


