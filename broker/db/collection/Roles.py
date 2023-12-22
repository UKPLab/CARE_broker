from broker.db.utils import results
from broker.db.collection import Collection


class Roles(Collection):
    """
    Role Collection

    @author: Dennis Zyska
    """

    def __init__(self, db, adb, config, socketio):
        self.roles = ['guest', 'user', 'admin']
        self.cache = []

        super().__init__("roles", db, adb, config, socketio)

    def _init(self):
        """
        Initialize standard roles
        :return:
        """
        super()._init()

        # upsert standard roles
        for role in self.roles:
            cursor = results(self._sysdb.aql.execute(
                """
                    UPSERT {
                        name: @name
                    }
                    INSERT {
                        name: @name,
                        quota: @quota,
                        created: DATE_NOW(),
                        updated: DATE_NOW(),
                        updates: 0,
                        room: @room
                    }
                    UPDATE {
                        quota: @quota,
                        updated: DATE_NOW(),
                        updates: OLD.updates + 1,
                        room: @room
                    }
                    IN @@collection
                    RETURN NEW
                """,
                bind_vars={
                    "@collection": self.name,
                    'name': role,
                    'quota': self.config['quota'][role] if role in self.config['quota'] else 0,
                    'room': "role:" + role
                }))

    def get_all(self, force=False):
        """
        Get all roles
        :param force: force reload from db
        :return:
        """
        if force or len(self.cache) == 0:
            self.cache = [doc for doc in results(self.collection.find({}))]
        return self.cache

    def get(self, name, force=False):
        """
        Get role by name
        :param name: name of the role
        :param force: force reload from db
        :return:
        """
        if force or len(self.cache) == 0:
            roles = results(self.collection.find({"name": name}))
            if roles.count() > 0:
                return roles.next()
        else:
            role = [role for role in self.cache if role['name'] == name]
            if len(role) > 0:
                return role[0]
            else:
                return None

    def __call__(self, name, force=False):
        """
        Get role by name
        :param name: name of the role
        :param force: force reload from db
        :return:
        """
        return self.get(name, force)
