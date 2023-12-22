import importlib
import os

from broker.skills.SkillModel import SkillModel
from . import CLI


class Skills(CLI):
    def __init__(self):
        super().__init__()
        self.name = 'skills'
        self.help = "Menu for managing skills"
        self.parser_build = None
        self.parser_run = None
        self.parser_stop = None
        self.skills = {}
        self.model_path = "./broker/skills/models"

        self.load_skills()

    def load_skills(self):
        """
        Load all available skills
        :return:
        """
        for skill in os.listdir(self.model_path):
            if os.path.isdir(os.path.join(self.model_path, skill)):
                if os.path.isfile(os.path.join(self.model_path, "{}/Model.py".format(skill))):
                    module = importlib.import_module("broker.skills.models.{}.Model".format(skill))
                    model_class = getattr(module, "Model")

                    if issubclass(model_class, SkillModel):
                        model = model_class()
                        self.skills[model.name] = model
                    else:
                        print("Model {} is not a subclass of SkillModel".format(skill))

    def set_parser(self, parser):
        self.parser = parser
        model_parser = parser.add_subparsers(dest='skill_command', help="Commands for managing skills")
        parser_model_list = model_parser.add_parser('list', help="List available skills")

        self.parser_build = model_parser.add_parser('build', help="Build a skill")
        subparser = self.parser_build.add_subparsers(dest='name', help="Skill name to build")
        for skill in self.skills:
            skill_parser = subparser.add_parser(skill, help=self.skills[skill].help)
            skill_parser.add_argument('--nocache', help='Do not use cache', action='store_true')

        self.parser_run = model_parser.add_parser('run', help="Run a skill")
        subparser = self.parser_run.add_subparsers(dest='name', help="Skill name to run")
        for skill in self.skills:
            skill_parser = subparser.add_parser(skill, help=self.skills[skill].help)
            skill_parser.add_argument('--url', help='URL of the broker', default=os.environ.get('BROKER_URL'))
            skill_parser.add_argument('--num_containers', help='Number of containers to start (default: 1)', type=int,
                                      default=1)
            skill_parser.add_argument('--container_suffix',
                                      help="Add a suffix to container name to start different containers (Default = '')",
                                      default='')
            skill_parser.add_argument('--network', help='Network name (Default: network_broker)', type=str,
                                      default='network_broker')
            skill_parser.add_argument('--skill', help='Name of the skill', default='')
            self.skills[skill].set_parser(skill_parser)

        self.parser_stop = model_parser.add_parser('stop', help="Stop a skill")
        subparser = self.parser_stop.add_subparsers(dest='name', help="Skill name to stop")
        for skill in self.skills:
            skill_parser = subparser.add_parser(skill, help=self.skills[skill].help)
            skill_parser.add_argument('--timeout', help='Timeout for stopping the container (Default: 10)', default=10,
                                      type=int)
            skill_parser.add_argument('--only_stop', help='Only stop the container, do not remove it',
                                      action='store_true')

    def list_skills(self):
        """
        List all skills
        :return:
        """
        print("Available skills:")
        for skill in self.skills:
            print("- {}".format(skill))

    def handle(self, args):
        if args.skill_command == 'build':
            if args.name is not None and args.name in self.skills:
                self.skills[args.name].build(args.nocache)
            else:
                self.parser_build.print_help()
                exit()
        elif args.skill_command == 'list':
            self.list_skills()
        elif args.skill_command == 'run':
            if args.name is not None and args.name in self.skills:
                self.skills[args.name].run(args)
            elif args.name is not None:
                print("Skill {} not found".format(args.name))
                self.list_skills()
            else:
                self.parser_run.print_help()
                exit()
        elif args.skill_command == 'stop':
            if args.name is not None and args.name in self.skills:
                self.skills[args.name].stop(args)
            elif args.name is not None:
                print("Skill {} not found".format(args.name))
                self.list_skills()
            else:
                self.parser_stop.print_help()
                exit()
        else:
            self.parser.print_help()
            exit()
