import os

from broker.db.Database import Database


def connect_db(config, socketio):
    """
    Connect to the arango db with environment variables.
    :return:
    """
    url = "http://{}:{}".format(os.getenv("ARANGODB_HOST", "localhost"), os.getenv("ARANGODB_PORT", "8529"))
    password = os.getenv("ARANGODB_ROOT_PASSWORD", "root")
    db_name = os.getenv("ARANGODB_DB_NAME", "broker")
    db = Database(url=url, username="root", password=password, db_name=db_name, config=config, socketio=socketio)
    return db



