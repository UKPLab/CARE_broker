class SkillSimple:
    def __init__(self, name):
        self.name = name
        self.description = "This is just a template for a simple skill"

    def init(self):
        """
        Initialize the skill
        :return:
        """
        pass

    def get_config(self):
        """
        Register the skill at the broker
        :return: None
        """
        return {
            'name': self.name,
            'description': self.description,
            'input': self.get_input(),
            'output': self.get_output()
        }

    def execute(self, data):
        """
        Execute the skill
        :param data: data object from the broker
        :return: result object
        """
        return data, None

    def get_input(self):
        """
        Get the input schema
        :return:
        """
        return {
            'data': {
                '*': {
                    'type': 'string',
                    'required': True
                }
            },
            'example': {
                {'anything': 'Hello World'}
            }
        }

    def get_output(self):
        """
        Get the output schema
        :return:
        """
        return {
            'data': {
                '*': {
                    'type': 'string',
                    'required': True
                }
            },
            'example': {
                {'anything': 'Hello World'}
            }
        }
