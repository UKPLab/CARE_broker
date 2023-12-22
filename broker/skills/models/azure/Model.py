""" Skill for OpenAI Azure Client

This skill is a simple wrapper for the OpenAI Azure Client.

Documentation Azure Client
https://learn.microsoft.com/en-us/azure/ai-services/openai/quickstart?tabs=command-line%2Cpython-new&pivots=programming-language-python

Author: Dennis Zyska
"""
import docker

from broker.skills.SkillModel import SkillModel


class Model(SkillModel):
    def __init__(self):
        super().__init__('openai_azure')
        self.help = 'Open AI azure client'
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
                'AZURE_OPENAI_KEY': args.api_key,
                'AZURE_OPENAI_ENDPOINT': args.api_endpoint,
                'OPENAI_MODEL': args.model,
                'API_VERSION': "2023-05-15" if args.model == "gpt-4" else "2023-10-01-preview",
                'OPENAI_API_TYPE': "azure",
                'BROKER_URL': args.url,
                'SKILL_NAME': self.name if args.skill == "" else args.skill,
            },
        })

    def set_parser(self, parser):
        super().set_parser(parser)
        self.parser.add_argument('--api_key', help='OpenAI API Key', required=True)
        self.parser.add_argument('--api_endpoint', help='OpenAI API Endpoint', default='https://api.openai.com')
        self.parser.add_argument('--model', help='OpenAI Model (Default: gpt-35-turbo-0301',
                                 default='gpt-35-turbo-0301')

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
                path="./broker/skills/models/azure",
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
