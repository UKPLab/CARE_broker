""" Skill for Llama.cpp Models

This skill is a simple wrapper for the LLama.cpp python client

https://llama-cpp-python.readthedocs.io/en/latest/

Author: Dennis Zyska
"""
import docker
import os
from broker.skills.SkillModel import SkillModel


class Model(SkillModel):
    def __init__(self):
        super().__init__('llama.cpp')
        self.help = 'Llama.cpp client'
        self.template = 'simpleSkill'

    def run(self, args, additional_parameter=None):
        """
        Run the skill
        :param additional_parameter:
        :param args:
        :return:
        """
        model_path, model_file = os.path.split(args.model_path)

        super().run(args, {
            "environment": {
                'MODEL_PATH': os.path.join("/model", model_file),
                'N_THREADS': args.n_threads,
                'NUM_CTX': args.n_ctx,
                'BROKER_URL': args.url,
                'SKILL_NAME': self.name if args.skill == "" else args.skill,
            },
            "volumes": {
                model_path: {'bind': '/model', 'mode': 'ro'},
            }
        })

    def set_parser(self, parser):
        super().set_parser(parser)
        self.parser.add_argument('--model_path', help='Llama.cpp model', required=True)
        self.parser.add_argument('--n_threads', help='Number of threads for llama.cpp', type=int, default=30)
        self.parser.add_argument('--n_ctx', help='Contexts length for llama.cpp', type=int, default=512)

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
                path="./broker/skills/models/llama_cpp",
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
