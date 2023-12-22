from datetime import datetime

from broker.db.collection import Collection
from broker.db.utils import results


class Skills(Collection):
    """
    Skill Collection

    @author: Dennis Zyska
    """

    def __init__(self, db, adb, config, socketio):
        super().__init__("skills", db, adb, config, socketio)
        self.quotas = {}

        self.index = results(self.collection.add_hash_index(fields=['sid'], name='sid_index', unique=False))
        self.index = results(self.collection.add_hash_index(fields=['connected'], name='connected_index', unique=False))

    def register(self, sid, data):
        """
        Register a new skill

        :param sid: session id of skill node
        :param data: skill data
        """
        skills = self.get_skills(filter_name=data['name'], with_config=True)
        if len(skills) > 0:
            print(skills)
            if not skills[0]['config'] == data:
                self.socketio.emit("error", {"code": 201}, to=sid)
                return

        skill = {
            "sid": sid,
            "config": data,
            "connected": True,
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat(),
            "last_contact": datetime.now().isoformat(),
            "first_contact": datetime.now().isoformat(),
        }

        results(self.collection.insert(
            skill
        ))
        self.send_update(skill['config']['name'])

    def unregister(self, sid):
        """
        Unregister all skills from a node

        :param sid: session id of skill node
        """
        skills = results(self.collection.find({"sid": sid, "connected": True}))
        for skill in skills:
            # send update first
            self.send_update(skill['config']['name'], config=skill['config'])

            skill["connected"] = False
            skill["last_contact"] = datetime.now().isoformat()
            results(self.collection.update(skill))

    def send_update(self, skill_name, config=None, **kwargs):
        """
        Send update to all connected clients

        If name is given, only send update for this skill

        :param skill_name: name of the skill
        :param config: config of the skill (for disconnect)
        :param kwargs: additional arguments for socketio.emit
        """
        nodes = 0
        skill = self.get_skills(filter_name=skill_name, with_config=True if config is None else False)
        if len(skill) > 0:
            nodes = skill[0]['nodes']
            if 'config' in skill[0]:
                config = skill[0]['config']
        if config is not None and 'roles' in config and len(config['roles']) > 0:
            for role in config['roles']:
                self.socketio.emit("skillUpdate", [{"name": skill_name, "nodes": nodes}],
                                   to="role:{}".format(role), **kwargs)
        else:
            self.socketio.emit("skillUpdate", [{"name": skill_name, "nodes": nodes}], **kwargs)

    def send_all(self, role, with_config=False, **kwargs):
        """
        Send update to all connected clients
        :param with_config:
        :param role: filter skills for role
        :param kwargs:
        :return:
        """
        all_skills = self.get_skills(filter_role=role, with_config=with_config)

        if all_skills:
            self.socketio.emit("skillUpdate", all_skills, **kwargs)

    def get_node(self, sid, name):
        """
        Get a random node by name

        :param name: Skill name
        :param sid: session id of the requested user
        :return: random node id (session id)
        """
        user = self.db.clients.get(sid)
        aql_query = """
                FOR doc IN @@collection
                FILTER doc.connected 
                FILTER (!HAS("roles", doc.config) or @role IN doc.config.roles)
                FILTER doc.config.name == @name
                SORT RAND()
                LIMIT 1
                RETURN doc
            """
        cursor = results(
            self._sysdb.aql.execute(aql_query, bind_vars={"@collection": self.name, "role": user["role"], "name": name},
                                    count=True))

        if cursor.count() > 0:
            return cursor.next()

    def check_feature(self, key, feature, check_all=False):
        """
        Check if a feature is available for a skill
        :param key: db key
        :param feature: feature as string or list of features
        :param check_all: check if all features are available, otherwise only one is enough
        :return:
        """
        if key is None:
            return False
        if isinstance(feature, str):
            feature = [feature]

        skill = self.get(key)
        if 'features' in skill['config']:
            if check_all:
                return all(f in skill['config']['features'] for f in feature)
            else:
                return any(f in skill['config']['features'] for f in feature)
        else:
            return False

    def get_skill(self, name):
        """
        Get a skill by name (aggregated, only first config is used)

        :param name: Skill name
        """
        return results(self.collection.find({"config.name": name, "connected": True}, limit=1))

    def get_skills(self, filter_name=None, filter_role=None, with_config=False):
        """
        Get list of skills (aggregated)

        :param with_config: with config
        :param filter_name: filter by name
        :param filter_role: filter by role
        :return: list of skills
        """
        skills = []

        filtering = {
            "filter_name": "FILTER doc.config.name == @name"
            if filter_name is not None else "",
            "filter_role": "FILTER @role == 'admin'"
                           "or !HAS(doc.config, 'roles') "
                           "or LENGTH(doc.config.roles) == 0 "
                           "or @role IN doc.config.roles"
            if filter_role is not None else "",
            "return": "RETURN { name: name, nodes: nodes }"
        }
        aql_query = """
            FOR doc IN @@collection
            FILTER doc.connected 
            {filter_name}
            {filter_role}
            COLLECT name = doc.config.name, node = doc.config.name WITH COUNT INTO nodes
            {return}
        """.format(**filtering)
        bind_vars = {"@collection": self.name}
        if filter_name is not None:
            bind_vars["name"] = filter_name
        if filter_role is not None:
            bind_vars["role"] = filter_role
        cursor = results(self._sysdb.aql.execute(aql_query, bind_vars=bind_vars, count=True))
        for skill in cursor:
            if with_config:
                skill["config"] = self.get_skill_config(skill['name'])
            skills.append(skill)
        return skills

    def get_skill_config(self, name):
        """
        Get a skill config by name

        :param name: Skill name
        """

        aql_query = """
                    FOR doc IN @@collection
                    FILTER doc.connected 
                    FILTER doc.config.name == @name
                    RETURN doc
                """
        bind_vars = {"@collection": self.name, "name": name}
        cursor = results(self._sysdb.aql.execute(aql_query, bind_vars=bind_vars, count=True))
        if cursor.count() > 0:
            skill_data = cursor.next()
            return skill_data["config"] if "config" in skill_data else {}
        else:
            return {}

    def clean(self):
        """
        Clean up database
        """
        cleaned = results(self.collection.update_match({"connected": True}, {"connected": False, "cleaned": True}))
        self.logger.info("Cleaned up {} skills".format(cleaned))
