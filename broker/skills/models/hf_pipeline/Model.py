""" Skill for the Huggingface Pipeline

This skill is a simple wrapper for the Huggingface Pipeline:

https://huggingface.co/docs/transformers/main_classes/pipelines

Author: Dennis Zyska
"""
import docker
import os
from broker.skills.SkillModel import SkillModel


class Model(SkillModel):
    def __init__(self):
        super().__init__('hf_pipeline')
        self.help = 'Huggingface pipeline client'
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
                'TASK': args.task,
                'MODEL': args.model,
                'CUDA_DEVICE': args.cuda,
                'BROKER_URL': args.url,
                'SKILL_NAME': self.name if args.skill == "" else args.skill,
            },
        })

    def set_parser(self, parser):
        super().set_parser(parser)
        tasks_files = os.listdir('./broker/skills/models/hf_pipeline/tasks')
        tasks = [os.path.splitext(file)[0] for file in tasks_files if file.endswith('.yaml')]

        self.parser.add_argument('--task', help='Huggingface pipeline task', choices=tasks, required=True)
        self.parser.add_argument('--model', help='Overwrite basic huggingface pipeline model', default="")
        self.parser.add_argument('--cuda', help='CUDA device', default=-1, type=int)

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
                path="./broker/skills/models/hf_pipeline",
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
