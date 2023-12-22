import subprocess

from . import CLI


class Broker(CLI):
    def __init__(self):
        super().__init__()
        self.name = 'broker'
        self.help = "Menu for managing broker"
        self.assign_parser = None

    def set_parser(self, parser):
        self.parser = parser
        parser.add_argument('--env', help="Environment file to load", type=str, default="")

        sub_parser = parser.add_subparsers(dest='sub_command', help="Commands for managing broker")
        build_parser = sub_parser.add_parser('build', help="Build the broker")
        build_parser.add_argument('--no-cache', help="Do not use cache", action='store_true')
        build_parser.add_argument('--network', help="Network name (Default: network_broker)", type=str,
                                  default='network_broker')

    def handle(self, args):
        if args.sub_command == 'build':
            # running subprocess to build the broker
            process = None
            try:
                process = subprocess.Popen(
                    ['docker', 'compose', '-f', 'docker-compose.yml', '-p', args.network, 'up', '--build', '-d'],
                    # Replace 'up' with your desired Docker Compose command
                    cwd=".",  # Path to your Docker Compose subdirectory
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )

                for line in process.stdout:
                    # Print live output
                    print(line, end='')

                process.communicate()  # Wait for the process to complete

            except KeyboardInterrupt:
                print("Keyboard interrupt")
            finally:
                if process is not None:
                    try:
                        process.terminate()
                    except OSError:
                        process.kill()

        if args.sub_command == 'scrub':
            pass
        elif args.sub_command == 'init':
            pass
        elif args.sub_command == 'assign':
            pass
        else:
            self.parser.print_help()
            exit()
