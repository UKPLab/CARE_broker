import logging
import multiprocessing as mp
import os
import time

import socketio

from broker import init_logging, load_config
from broker.db import connect_db
from Crypto.PublicKey import RSA


def simple_client(name, url, client_queue: mp.Queue, message_queue: mp.Queue, skill_queue: mp.Queue = None,
                  skill_name="test_skill",
                  logging_level="INFO"):
    logger = init_logging(name, level=logging.getLevelName(logging_level))
    sio = socketio.Client(logger=logger, engineio_logger=logger)

    @sio.on('skillUpdate')
    def skill_update(data):
        logger.debug("skillUpdate: {}".format(data))
        if skill_queue:
            skill_queue.put(data)
        if len(data) > 0:
            for skill in data:
                if skill['name'] == skill_name:
                    sio.emit('skillGetConfig', {'name': skill['name']})

    sio.on('connect', lambda: [sio.emit('skillGetAll'), client_queue.put("connected")])
    sio.on('skillConfig', lambda data: logger.debug("skillConfig: {}".format(data)))
    sio.on('skillResults', lambda data: [logger.debug("Skill results: {}".format(data)), client_queue.put(data)])

    # connect to Broker
    while True:
        if sio.connected:
            logger.debug("Waiting for next message...")
            message = message_queue.get()
            sio.emit('skillRequest', message)
            logger.debug("Send message: {}".format(message))
        else:
            try:
                sio.connect(url)
            except socketio.exceptions.ConnectionError:
                logger.error("Connection to broker failed. Trying again in 5 seconds ...")
                time.sleep(5)


def scrub_job(overwrite_config=None):
    """
    Simple job to start a scrub process (e.g., by an cronjob)
    :return:
    """
    logger = init_logging("Scrub Job", level=logging.getLevelName("INFO"))
    logger.info("Connecting to db...")
    config = load_config()
    if overwrite_config:
        config.update(overwrite_config)

    db = connect_db(config, None)
    db.tasks.scrub(run_forever=False)


def init_job():
    """
    Reinit the database with new keys for system user
    :return:
    """
    logger = init_logging("Init Job", level=logging.getLevelName("INFO"))

    logger.info("Loading config...")
    config = load_config()

    logger.info("Connecting to db...")
    db = connect_db(config, None)
    db.users.reinit(private_key_path="./private_key.pem")


def check_key(private_key_path="private_key.pem", length=1024, create=False):
    """
    Check if key file exists
    :param private_key_path: path to key file
    :param length: length of key
    :param create: create key if not exists
    :return:
    """
    if not os.path.exists(private_key_path):
        if create:
            key = RSA.generate(length)
            with open(private_key_path, "wb") as f:
                f.write(key.export_key("PEM"))
                print("Key written to {}".format(private_key_path))
        else:
            print("Key file not found: {}".format(private_key_path))
            exit(1)
    else:
        print("Key file found: {}".format(private_key_path))
