import random
from datetime import datetime
from uuid import uuid4

from broker import init_logging
from broker.db import results


class Skills:
    """
    Represents skills from the database

    @author: Dennis Zyska
    """

    def __init__(self, db, socketio):
        self.socketio = socketio
        self.logger = init_logging("skills")

        if results(db.has_collection("skills")):
            self.db = db.collection("skills")
        else:
            self.db = results(db.create_collection("skills"))

        self.index = results(self.db.add_hash_index(fields=['sid'], name='sid_index', unique=False))
        self.index = results(self.db.add_hash_index(fields=['connected'], name='connected_index', unique=False))

        self.clean()

    def register(self, sid, data):
        """
        Register a new skill

        :param sid: session id of skill node
        :param data: skill data
        """
        results(self.db.insert(
            {
                "uid": str(uuid4()),
                "sid": sid,
                "config": data,
                "connected": True,
                "created": datetime.now().isoformat(),
                "updated": datetime.now().isoformat(),
                "last_contact": datetime.now().isoformat(),
                "first_contact": datetime.now().isoformat(),
                "reconnects": 1,
            }
        ))
        self.send_update(data["name"])

    def unregister(self, sid):
        """
        Unregister a skill

        :param sid: session id of skill node
        """
        skills = results(self.db.find({"sid": sid, "connected": True}))
        if len(skills) > 0:
            skill = skills.next()
            skill["connected"] = False
            skill["last_contact"] = datetime.now().isoformat()
            results(self.db.update(skill))
            self.send_update(skill["config"]["name"])

    def send_update(self, name=None, with_config=False, **kwargs):
        """
        Send update to all connected clients

        If name is given, only send update for this skill

        :param name: name of skill
        :param with_config: send with config
        :param kwargs: additional arguments for socketio.emit
        """
        if name:
            self.socketio.emit("skillUpdate", [self.get_skill(name, with_config=with_config)], **kwargs)
        else:
            all_skills = self.get_skills(with_config=with_config)
            self.socketio.emit("skillUpdate", [all_skills[key] for key in all_skills.keys()], **kwargs)

    def get_node(self, name):
        """
        Get a random node by name

        :param name: Skill name
        :return: random node id (session id)
        """
        skills = results(self.db.find({"config.name": name, "connected": True}))
        if len(skills) == 0:
            return None

        pos = random.randint(0, len(skills) - 1)
        for i in range(0, pos):
            skill = skills.next()
        return skills.next()["sid"]

    def get_skill(self, name, with_config=False):
        """
        Get a skill by name (aggregated, only first config is used)

        :param name: Skill name
        :param with_config: with config
        """
        skills = results(self.db.find({"config.name": name, "connected": True}))
        if len(skills) == 0:
            return {
                "nodes": 0,
                "name": name,
            }

        skill = skills.next()
        data = {
            "nodes": len(skills),
            "name": skill["config"]["name"],
        }
        if with_config:
            data["config"] = skill["config"]
        return data

    def get_skills(self, with_config=False):
        """
        Get list of skills (aggregated)

        :param with_config: with config
        """
        skills = results(self.db.find({"connected": True}))
        skill_list = {}
        for skill in skills:
            name = skill["config"]["name"]
            if name not in skill_list:
                skill_list[name] = {
                    "nodes": 1,
                    "name": name,
                }
                if with_config:
                    skill_list[name]["config"] = skill["config"]
            else:
                skill_list[name]["nodes"] += 1
        return skill_list

    def clean(self):
        """
        Clean up database
        """
        cleaned = results(self.db.update_match({"connected": True}, {"connected": False, "cleaned": True}))
        self.logger.info("Cleaned up {} skills".format(cleaned))
