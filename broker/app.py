"""
Broker entry point for bootstrapping the server

This is the file used to start the flask (and socketio) server.
"""

from eventlet import monkey_patch  # mandatory! leave at the very top

monkey_patch()

from flask import Flask, session, request
from flask_socketio import SocketIO

from broker.sockets.Request import Request
from broker.sockets.Skill import Skill

from broker.sockets.Auth import Auth
import os
from broker import init_logging, load_config, load_env
from broker.db import connect_db
import random
import string
import redis
import argparse

__author__ = "Dennis Zyska, Nils Dycke"
__credits__ = ["Dennis Zyska", "Nils Dycke"]


def parser():
    """
    Parser for the CLI
    :return:
    """
    arg_parser = argparse.ArgumentParser(description='Broker Server')
    arg_parser.add_argument('--env', help="Environment file to load (Default using ENV)", type=str, default="")
    sub_parser = arg_parser.add_subparsers(dest='broker_command', help="Commands for broker")
    sub_parser.add_parser('scrub', help="Only run scrub job")
    sub_parser.add_parser('init', help="Init the broker")

    a_parser = sub_parser.add_parser('assign', help="Assign a role to a user")
    a_parser.add_argument('--role', help="Assign role to user (Default: admin)", type=str, default='admin')
    a_parser.add_argument('--key', help="Public key of user for assigning a role", type=str, default=None)
    return arg_parser, a_parser


def init():
    """
    Initialize the flask app and check for the connection to the GROBID client.
    :return:
    """
    logger = init_logging("broker")

    config = load_config()

    logger.info("Initializing server...")
    # flask server
    app = Flask("broker")
    app.config.update({
        "SECRET_KEY": ''.join(random.choice(string.printable) for i in range(8)),
        "SESSION_TYPE": "redis",
        "SESSION_PERMANENT": False,
        "SESSION_USE_SIGNER": True,
        "SESSION_REDIS": redis.from_url("redis://{}:{}".format(os.getenv("REDIS_HOST"), os.getenv("REDIS_PORT")), )
    })
    socketio = SocketIO(app, cors_allowed_origins='*', logger=logger, engineio_logger=logger)

    # get db and collection
    logger.info("Connecting to db...")
    db = connect_db(config, socketio)

    # add socket routes
    logger.info("Initializing socket...")
    sockets = {
        "request": Request(db=db, socketio=socketio),
        "auth": Auth(db=db, socketio=socketio),
        "skill": Skill(db=db, socketio=socketio)
    }

    # socketio
    @socketio.on("connect")
    def connect(data):
        """
        Example connection event. Upon connection on "/" the sid is loaded, stored in the session object
        and the connection is added to the room of that SID to enable an e2e connection.

        :return: the sid of the connection
        """
        db.clients.connect(sid=request.sid, ip=request.remote_addr, data=data)
        session["sid"] = request.sid

        logger.debug(f"New socket connection established with sid: {request.sid} and ip: {request.remote_addr}")

        return request.sid

    @socketio.on("disconnect")
    def disconnect():
        """
        Disconnection event

        :return: void
        """
        db.clients.disconnect(sid=request.sid)

        logger.debug(f"Socket connection teared down for sid: {request.sid}")

    app_config = {
        "debug": os.getenv("FLASK_DEBUG", False),
        "host": "0.0.0.0",
        "port": os.getenv("BROKER_PORT", 4852)
    }
    logger.info("App starting ...", app_config)
    socketio.run(app, **app_config, log_output=True)


if __name__ == '__main__':
    logger = init_logging("main")

    # argument parser
    parser, assign_parser = parser()
    args = parser.parse_args()

    # load env
    load_env(args.env)

    if args.broker_command == 'scrub':
        from broker.utils import scrub_job

        scrub_job()
    elif args.broker_command == 'init':
        from broker.utils import init_job, check_key

        check_key(create=True)
        init_job()
    elif args.broker_command == 'assign':
        if args.key is None or args.role is None:
            assign_parser.print_help()
            exit()

        config = load_config()
        config['cleanDbOnStart'] = False
        config['scrub']['enabled'] = False
        config['taskKiller']['enabled'] = False
        db = connect_db(config, None)

        user = db.users.set_role(args.key, args.role)
        if user:
            logger.info("Role assigned to user, db entry: {}".format(user['_key']))
        else:
            logger.error("User not found in db, please check the public key")
    else:
        init()
