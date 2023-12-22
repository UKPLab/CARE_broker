""" Skill for Vader Sentiment Analysis

Author: Dennis Zyska, Nils Dycke
"""

from SkillSimple import SkillSimple
from nltk.sentiment.vader import SentimentIntensityAnalyzer


class Skill(SkillSimple):
    """
    Skill for Llama.cpp Models
    """

    def __init__(self, name):
        super().__init__(name)
        self.description = "This is a skill for the Vader Sentiment Analysis"
        self.vader = None

    def init(self):
        """
        Initialize Open AI Connection
        :return:
        """
        self.vader = SentimentIntensityAnalyzer()

    def execute(self, data):
        """
        Execute a request to the OpenAI API
        :param data:
        :return:
        """
        polarity = [x for x in self.vader.polarity_scores(data['data']["text"]).items() if x[0] != "compound"]
        polarity.sort(key=lambda x: x[1], reverse=True)

        response = {'score': polarity[0][1], "label": polarity[0][0]}

        # return None, None
        return response, None

    def get_input(self):
        """
        Get the input schema
        :return:
        """
        return {
            'data': {
                'text': {
                    'type': 'string',
                    'required': True,
                    'description': 'The text to be classified'
                },
            },
            'example': {
                'text': 'This restaurant is awesome!',
            }
        }

    def get_output(self):
        """
        Get the output schema
        :return:
        """
        return {
            'data': {
                'score': {
                    'type': 'float',
                    'description': "The score of the sentiment analysis"
                },
                'label': {
                    'type': 'string',
                    'description': "The label of the sentiment analysis"
                }
            },
            'example': {
                'score': 0.9,
                'label': "pos"
            }
        }
