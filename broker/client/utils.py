import logging
import multiprocessing as mp
import time

import socketio

from broker import init_logging


def client_process(name, url, in_queue: mp.Queue, out_queue: mp.Queue):
    logger = init_logging(name, level=logging.getLevelName("INFO"))
    sio = socketio.Client(logger=logger, engineio_logger=logger)

    @sio.on('*')
    def catch_all(event, data):
        out_queue.put({"event": event, "data": data})

    sio.on('connect', lambda: [out_queue.put({"event": "connected", "data": {}})])

    # always send task requests back to broker

    @sio.on('taskRequest')
    def task_request(data):
        out_queue.put({"event": "taskRequest", "data": data})
        if isinstance(data['data'], dict) and 'sleep' in data['data']:
            time.sleep(data['data']['sleep'])
        sio.emit('taskResults', {"id": data["id"], "data": data['data']})

    while True:
        try:
            if sio.connected:
                logger.debug("Waiting for next message...")
                message = in_queue.get()
                sio.emit(message['event'], message['data'])
                logger.debug("Send message: {}".format(message))
            else:
                sio.connect(url)
        except socketio.exceptions.ConnectionError:
            logger.error("Connection to broker failed. Trying again in 5 seconds ...")
            time.sleep(5)
