"""
This is a simple skill template for building the container of a model.

Author: Dennis Zyska
"""
import docker

from broker.cli import CLI
from broker.skills.templates.simpleSkill import create_docker as build_simple_skill


class SkillModel(CLI):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.tag = 'broker_skill_' + self.name
        self.template = "simpleSkill"

    def set_parser(self, parser):
        self.parser = parser

    def build(self, nocache=False):
        """
        Build the docker container
        :param nocache: Do not use cache
        :return:
        """
        if self.template is None:
            print("No template defined")
            exit()
        if self.template == "simpleSkill":
            build_simple_skill(nocache=nocache)

    def run(self, args, additional_parameter=None):
        """
        Run the skill
        :param additional_parameter: Additional parameters for the container
        :param args: CLI arguments
        :return:
        """
        # Check if the container is already built
        client = docker.from_env()
        try:
            print("Running skill {}".format(self.name))

            image = client.images.get(self.tag)
            print("Found image {}".format(image.short_id))

            print("Stop currently running containers...")
            self.stop(args)

            print("Check network exists...")
            network = {}
            try:
                net = client.networks.get(args.network)
                if net:
                    network = {'network': args.network}
            except docker.errors.NotFound:
                print("Network not found.")

            # Run the container
            for i in range(1, args.num_containers + 1):
                container = client.containers.run(
                    self.tag,
                    name="{}_{}".format(self.tag, i)
                    if args.container_suffix == "" else
                    "{}_{}_{}".format(self.tag, args.container_suffix, i),
                    detach=True,
                    command='python3 /app/connect.py',
                    restart_policy={"Name": "always"},
                    **additional_parameter,
                    **network
                )
                print("Build container {}".format(container.short_id))
                print(container.logs().decode('utf-8'))

        except docker.errors.ImageNotFound:
            print("Image not found. Please build the container first.")
            exit()

    def stop(self, args):
        """
        Stop the skill
        :param args:
        :return:
        """
        containers = self.get_containers()
        if args.container_suffix != "":
            containers = [container for container in containers if
                          container.name.removeprefix("{}_".format(self.tag)).startswith(args.container_suffix)]
        for container in containers:
            try:
                container.stop(timeout=args.timeout if "timeout" in args else 10)
                container.wait()
            except docker.errors.APIError:
                container.kill()
            print("Stopped container {}".format(container.name))
            if "only_stop" not in args:
                container.remove(force=True)
                print("Removed container {}".format(container.name))

    def get_containers(self):
        """
        Get all running containers
        :return:
        """
        client = docker.from_env()
        return [container for container in client.containers.list(all=True) if container.name.startswith(self.tag)]
