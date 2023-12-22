""" Skill for the Huggingface Pipeline

This skill is a simple wrapper for the Huggingface Pipeline:

https://huggingface.co/docs/transformers/main_classes/pipelines

Author: Dennis Zyska
"""

import os

from SkillSimple import SkillSimple
from transformers import pipeline
import yaml


class Skill(SkillSimple):
    """
    Skill for OpenAI API
    """

    def __init__(self, name):
        self.task = os.environ.get('TASK')
        with open("/app/{}.yaml".format(self.task), "r") as f:
            self.yaml = yaml.load(f, Loader=yaml.FullLoader)
        print("Config:")
        print(self.yaml)

        super().__init__(self.yaml['name'])
        self.description = self.yaml['description']
        self.pipe = None
        self.model = os.environ.get('MODEL') if os.environ.get('MODEL') != "" else self.yaml['pipeline']['model']
        self.task = self.yaml['pipeline']['task']

    def init(self):
        """
        Initialize Open AI Connection
        :return:
        """
        self.pipe = pipeline(task=self.task,
                             model=self.model,
                             device=int(os.environ.get('CUDA_DEVICE')))

    def execute(self, data):
        """
        Execute a request to the OpenAI API
        :param data:
        :return:
        """
        response = self.pipe(**data)
        return response, None

    def get_input(self):
        """
        Get the input schema
        :return:
        """
        return self.yaml['input']

    def get_output(self):
        """
        Get the output schema
        :return:
        """
        return self.yaml['output']