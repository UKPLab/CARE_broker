""" Skill for Llama.cpp Models

This skill is a simple wrapper for the LLama.cpp python client

https://llama-cpp-python.readthedocs.io/en/latest/

Author: Dennis Zyska
"""

import os

from SkillSimple import SkillSimple
from llama_cpp import Llama, LlamaGrammar


class Skill(SkillSimple):
    """
    Skill for Llama.cpp Models
    """

    def __init__(self, name):
        super().__init__(name)
        self.description = "This is a skill for the Llama.cpp python client"
        self.client = None

    def init(self):
        """
        Initialize Open AI Connection
        :return:
        """
        self.client = Llama(model_path=os.environ.get('MODEL_PATH'),
                            n_threads=int(os.environ.get('N_THREADS')),
                            n_ctx=int(os.environ.get('NUM_CTX')))

    def execute(self, data):
        """
        Execute a request to the OpenAI API
        :param data:
        :return:
        """
        if 'grammar' in data:
            data['grammar'] = LlamaGrammar.from_string(data['grammar'])
        response = self.client(data['prompt'], **data['params'])

        # return None, None
        return response, None

    def get_input(self):
        """
        Get the input schema
        :return:
        """
        return {
            'data': {
                'prompt': {
                    'type': 'string',
                    'required': True
                },
                'params': {
                    'type': 'object',
                    'description': 'Additional parameters for the llama python client',
                    'required': False
                },
                'grammar': {
                    'type': 'string',
                    'required': False
                },
            },
            'example': {
                'prompt': 'Print Hello World',
            }
        }

    def get_output(self):
        """
        Get the output schema
        :return:
        """
        return {
            'data': {
                'response': {
                    'type': 'string',
                },
            },
            'example': {
                'response': 'Hello World',
            }
        }
