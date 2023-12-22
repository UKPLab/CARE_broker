""" Skill for Vader Sentiment Analysis

Author: Dennis Zyska, Nils Dycke
"""
import os

import docker

from broker.skills.SkillModel import SkillModel


class Model(SkillModel):
    def __init__(self):
        super().__init__('vader')
        self.help = 'Vader Sentiment Analysis'
        self.template = 'simpleSkill'

    def run(self, args, additional_parameter=None):
        """
        Run the skill
        :param additional_parameter:
        :param args:
        :return:
        """
        super().run(args, {
            "environment": {
                'BROKER_URL': args.url,
                'SKILL_NAME': self.name if args.skill == "" else args.skill,
            },
        })

    def set_parser(self, parser):
        super().set_parser(parser)

    def build(self, nocache=False):
        """
        Build the docker container
        :param nocache: Do not use cache
        :return:
        """
        super().build(nocache)

        # Create a Docker client
        client = docker.from_env()

        try:
            build_logs = client.api.build(
                dockerfile="Dockerfile",
                path="./broker/skills/models/vader",
                tag=self.tag,
                decode=True, rm=True,
                nocache=nocache,
            )
            # Print build output in real-time
            for chunk in build_logs:
                if 'stream' in chunk:
                    for line in chunk['stream'].splitlines():
                        print(line)
        except docker.errors.BuildError as e:
            print("Failed to build Docker image:", e)
