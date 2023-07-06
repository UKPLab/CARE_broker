""" app -- Bootstrapping the server

This is the file used to start the flask (and socketio) server. It is also the file considered
by the celery client to setup RPCs to the celery server.

At the moment, the file contains examples to test your setup and get a feeling for how
celery + socketio can work together.

Author: Nils Dycke, Dennis Zyska
"""

from eventlet import monkey_patch  # mandatory! leave at the very top

monkey_patch()

import sys
from flask import Flask, session, request
from flask_socketio import SocketIO
from broker.config.WebConfiguration import instance as WebInstance
from broker.db.Clients import Clients
from broker.db.Tasks import Tasks
from broker.db.Skills import Skills
from broker.sockets.Register import Register
from arango import ArangoClient
import os
from broker import init_logging

__version__ = os.getenv("BROKER_VERSION")
__author__ = "Dennis Zyska, Nils Dycke"
__credits__ = ["Dennis Zyska", "Nils Dycke"]


def init():
    """
    Initialize the flask app and check for the connection to the GROBID client.
    :return:
    """
    logger = init_logging("broker")

    # check if dev mode
    DEV_MODE = "--dev" in sys.argv
    DEBUG_MODE = "--debug" in sys.argv
    config = WebInstance(dev=DEV_MODE, debug=DEBUG_MODE)

    # arango db
    logger.info("Connecting to db...")
    db_client = ArangoClient(
        hosts="http://{}:{}".format(os.getenv("ARANGODB_HOST", "localhost"), os.getenv("ARANGODB_PORT", "8529")))
    sys_db = db_client.db('_system', username='root', password=os.getenv("ARANGODB_ROOT_PASSWORD", "root"))
    if not sys_db.has_database('broker'):
        sys_db.create_database('broker')
    sync_db = db_client.db('broker', username='root', password=os.getenv("ARANGODB_ROOT_PASSWORD", "root"))
    db = sync_db.begin_async_execution(return_result=True)

    logger.info("Initializing server...")
    # flask server
    app = Flask("broker")
    app.logger = logger
    app.config.update(config.flask)
    app.config.update(config.session)
    socketio = SocketIO(app, **config.socketio, logger=logger, engineio_logger=logger)

    # clients
    logger.info("Initializing db tables...")
    db.clear_async_jobs()
    clients = Clients(db, socketio)
    tasks = Tasks(db, socketio)
    skills = Skills(db, socketio)

    # add socket routes
    logger.info("Initializing socket routes...")
    routes = Register(socketio=socketio, tasks=tasks, skills=skills, clients=clients)

    # socketio
    @socketio.on("connect")
    def connect(data):
        """
        Example connection event. Upon connection on "/" the sid is loaded, stored in the session object
        and the connection is added to the room of that SID to enable an e2e connection.

        :return: the sid of the connection
        """
        logger.debug(data)

        clients.connect(sid=request.sid, ip=request.remote_addr, data=data)
        session["sid"] = request.sid

        # send available skills
        skills.send_update(to=request.sid)

        logger.debug(f"New socket connection established with sid: {request.sid} and ip: {request.remote_addr}")

        return request.sid

    @socketio.on("disconnect")
    def disconnect():
        """
        Disconnection event

        :return: void
        """
        # todo
        # terminate running jobs
        # clear pending results

        # close connection
        clients.disconnect(sid=request.sid)

        # remove skills by sid if exists
        skills.unregister(sid=request.sid)

        # Terminate running jobs
        # 1. Docker container disconnect
        # TODO send task eventually to the next node if available
        # 2. Client disconnect
        # TODO send cancel request via socket io emit to container

        logger.debug(f"Socket connection teared down for sid: {request.sid}")

    logger.info("App starting ...", config.app)
    socketio.run(app, **config.app, log_output=True)


if __name__ == '__main__':
    init()
