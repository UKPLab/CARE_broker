import logging
import os

import yaml
from dotenv import load_dotenv


def init_logging(name=None, level=logging.INFO):
    if name is None:
        logger = logging.getLogger()
    else:
        logger = logging.getLogger(name)
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(processName)-10s %(name)s %(levelname)-8s %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logger.setLevel(level)
    return logger


def load_config():
    with open("./config.yaml", "r") as f:
        return yaml.load(f, Loader=yaml.FullLoader)


def load_env(env_file=None):
    if env_file is None or env_file == "" or not os.path.exists(env_file):
        if os.getenv("ENV", None) is not None:
            load_dotenv(dotenv_path=".env.{}".format(os.getenv("ENV", None)))
        else:
            load_dotenv(dotenv_path=".env")
    else:
        load_dotenv(dotenv_path=env_file)


