""" Command line interface for the broker

Author: Dennis Zyska
"""
import argparse
import logging

from broker import init_logging
from broker.cli import register_client_module
from broker.cli.Broker import Broker
from broker.cli.Skills import Skills

if __name__ == '__main__':
    logger = init_logging("Broker Manager", logging.DEBUG)

    # Argument parser
    parser = argparse.ArgumentParser(description="Broker Manager")
    subparser = parser.add_subparsers(title="Broker Manager", dest='command')
    modules = {}
    register_client_module(modules, subparser, Skills)
    register_client_module(modules, subparser, Broker)

    # parse arguments
    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
    else:
        modules[args.command].handle(args)
