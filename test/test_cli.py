import json
import logging
import multiprocessing as mp
import os
import time
import unittest
import subprocess

from dotenv import load_dotenv

from broker import init_logging, load_config
from broker.app import init
from broker.db import connect_db
from broker.utils import scrub_job
from broker.utils.Guard import Guard
from broker.client import Client

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        return result.returncode, result.stdout
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stderr


class TestCLI(unittest.TestCase):
    """
    Test the command line interface
    @author: Dennis Zyska
    """
    _broker = None
    _container = None
    _client = None
    _logger = None

    @classmethod
    def setUpClass(cls):
        if os.getenv("TEST_URL", None) is None:
            if os.getenv("ENV", None) is not None:
                load_dotenv(dotenv_path=".env.{}".format(os.getenv("ENV", None)))
            else:
                load_dotenv(dotenv_path=".env")

        logger = init_logging(name="Unittest", level=logging.getLevelName(os.getenv("TEST_LOGGING_LEVEL", "INFO")))
        cls._logger = logger

    def test_help(self):
        """
        Test the help command
        :return:
        """
        # running external command
        self._logger.info("Test help command")

        return_code, output = run_command("python3 client.py -h")
        self.assertEqual(return_code, 0)


