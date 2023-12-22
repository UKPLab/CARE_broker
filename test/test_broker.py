import json
import logging
import multiprocessing as mp
import os
import time
import unittest

from dotenv import load_dotenv

from broker import init_logging, load_config
from broker.app import init
from broker.db import connect_db
from broker.utils import scrub_job
from broker.utils.Guard import Guard
from broker.client import Client


class TestBroker(unittest.TestCase):
    """
    Test the broker
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

        logger.info("Load config ...")
        config = load_config()
        cls._config = config

        logger.info("Connect to db...")
        logger.info("http://{}:{}".format(os.getenv("ARANGODB_HOST", "localhost"), os.getenv("ARANGODB_PORT", "8529")))
        cls._db = connect_db(config, None)

        logger.info("Starting broker ...")
        logger.info("Broker URL: {}".format(os.getenv("TEST_URL")))
        logger.info("Broker Token: {}".format(os.getenv("TEST_TOKEN")))
        logger.info("Broker Skill: {}".format("test_skill"))
        logger.info("Start Broker? {}".format(os.getenv("TEST_START_BROKER")))
        if int(os.getenv("TEST_START_BROKER")) == 0:
            logger.info("Skip creating broker.")
        else:
            ctx = mp.get_context('spawn')
            broker = ctx.Process(target=init, args=())
            broker.start()
            cls._broker = broker

        logger.info("Starting response container ...")
        container = Client(logger=logger, url=os.getenv("TEST_URL"))
        ready = container.start()
        if not ready:
            logger.error("Container not ready by time. Exiting ...")
            logger.error(ready)
            exit(1)
        # register basic skill
        container.put({"event": "skillRegister", "data": {
            "name": "test_skill"
        }})
        cls._container = container

        logger.info("Starting client for testing that the environment is working ...")
        client = Client(logger=logger, url=os.getenv("TEST_URL"))
        ready = client.start()
        if not ready:
            logger.error("Environment not ready by time. Exiting ...")
            exit(1)
        if client.check_skill("test_skill"):
            logger.info("Environment ready!")
        else:
            logger.error("Environment not ready by time. Exiting ...")
            exit(1)
        client.stop()

    @classmethod
    def tearDownClass(cls):
        cls._logger.info("Stopping response container ...")
        cls._container.stop()

        cls._logger.info("Stopping broker ...")
        if int(os.getenv("TEST_START_BROKER")) == 0:
            cls._logger.info("Skip stopping broker.")
        else:
            cls._broker.terminate()
            cls._broker.join()

    def setUp(self) -> None:
        self._logger.info("Start new client ...")
        self.client = Client(os.getenv("TEST_URL"), logger=self._logger)
        unittest.skipIf(not self.client.start(), "Environment not ready by time. Skipping ...")
        time.sleep(0.5)
        self.client.clear()

    def tearDown(self) -> None:
        self._logger.info("Stop client ...")
        self.client.stop()

    def test_simple_request(self):
        """
        Test if a simple request is working
        :return:
        """
        self._logger.info("Start test simple request ...")
        self.client.clear()

        self.client.put(
            {"event": 'skillRequest', "data": {'id': "simple", 'name': "test_skill", 'data': time.perf_counter()}})

        self._logger.info("Wait for response ...")

        result = self.client.wait_for_event("skillResults")
        if result is None or not result:
            self.fail("No message received.")
        else:
            message = result['data']

        self._logger.info("Simple response time: {:3f}ms".format((time.perf_counter() - message['data']) * 1000))
        self.assertEqual(message['id'], "simple")
        return message['id'] == "simple"

    def test_stats(self):
        """
        Test if stats are returned if config['return_stats'] is set to True
        :return:
        """
        self._logger.info("Start test stats ...")
        self.client.put({"event": 'skillRequest', "data": {'id': "stats", 'name': "test_skill",
                                                           'config': {'return_stats': True},
                                                           'data': time.perf_counter()}})

        self._logger.info("Wait for response ...")

        message = self.client.wait_for_event("skillResults")
        self._logger.info("Stats Main process received message: {}".format(message))
        message = self.client.find_results("stats")

        self._logger.info("Simple response time: {:3f}ms".format((time.perf_counter() - message['data']) * 1000))
        self.assertEqual(message['id'], "stats")
        self.assertTrue("stats" in message)
        self._logger.info("Simple duration time: {:3f}ms".format((time.perf_counter() - message['data']) * 1000))

    def test_config(self):
        """
        Test different keyword arguments for the config parameter
        :return:
        """
        self._logger.info("Start test config ...")
        self.client.put({"event": 'skillRequest', "data": {'id': "stats1", 'name': "test_skill",
                                                           'config': {'return_stats': True},
                                                           'data': time.perf_counter()}})
        self.client.put({"event": 'skillRequest', "data": {'id': "stats2", 'name': "test_skill",
                                                           'data': time.perf_counter()}})
        self.client.put({"event": 'skillRequest', "data": {'id': "stats3", 'name': "test_skill",
                                                           'config': {},
                                                           'data': time.perf_counter()}})

        self._logger.info("Wait for response ...")

        self.client.wait_for_event("skillResults")
        self.client.wait_for_event("skillResults")
        self.client.wait_for_event("skillResults")
        message1 = self.client.find_results("stats1")
        message2 = self.client.find_results("stats2")
        message3 = self.client.find_results("stats3")

        self.assertEqual(message1['id'], "stats1")
        self.assertEqual(message2['id'], "stats2")
        self.assertEqual(message3['id'], "stats3")

    def test_attack(self):
        """
        Attacks Broker with fault requests
        :return:
        """
        self._logger.info("Start test attack ...")
        self.client.put({"event": 'skillRequest', "data": {}})
        self.client.put({"event": 'skillRequest', "data": ""})
        self.client.put({"event": 'skillRequest', "data": []})
        self.client.put({"event": 'skillRequest', "data": "Test"})
        self.client.put({"event": 'skillRequest', "data": {'1': "2"}})
        self.client.put({"event": 'skillRequest', "data": [1, 2, 3]})
        self.client.put({"event": 'skillRequest', "data": 1})
        self.client.put({"event": 'skillRequest', "data": True})

        self.client.clear()

        self.assertTrue(self.test_simple_request())

    def test_guard(self):
        """
        Test if guard is working
        :return:
        """
        self._logger.info("Start test guard ...")
        self._logger.info("Start client ...")
        ctx = mp.get_context('spawn')

        guard = Guard(os.getenv("TEST_URL"))
        client = ctx.Process(target=guard.run,
                             args=())
        client.start()

        # wait a second
        time.sleep(1)
        self.assertTrue(client.is_alive())
        client.terminate()
        client.join()

    def stressTest(self):
        """
        Stress test for broker with multiple clients
        :return:
        """
        self._logger.info("Start stress test ...")
        test_start = time.perf_counter()
        max_clients = int(os.getenv("TEST_STRESS_MAX_CLIENTS"))
        max_container = int(os.getenv("TEST_STRESS_MAX_CONTAINER"))
        max_messages = int(os.getenv("TEST_STRESS_MAX_MESSAGES"))

        # save all results in a file
        with open(os.getenv("TEST_RESULTS"), "w") as file:

            containers = []
            clients = []

            # add csv header
            header = [
                "time",
                "duration_container",
                "duration_request",
                "client",
                "container",
                "delay",
                "message_id",
                "data_length",
                "current_clients",
                "current_containers",
                "max_clients",
                "max_containers",
                "max_messages",
            ]
            file.write("{}\n".format(",".join(header)))

            def client_check(c):
                m = c.check_queue()
                if m:
                    if 'event' in m and m['event'] == "skillResults":
                        data = [
                            time.perf_counter() - test_start,  # time
                            m['data']['stats']['duration'],  # duration_container
                            time.perf_counter() - m['data']['data']['start'],  # duration_request
                            m['data']['data']['client'],  # client
                            m['data']['stats']['host'],  # container
                            m['data']['data']['delay'],  # delay
                            m['data']['data']['message'],  # message_id
                            len(json.dumps(m['data']['data'])),  # data_length
                            len(clients),  # current_clients
                            len(containers),  # current_containers
                            max_clients,  # max_clients
                            max_container,  # max_containers
                            max_messages,  # max_messages
                        ]

                        file.write("{}\n".format(",".join(str(e) for e in data)))

            self._logger.info("Start stress test ...")
            for container_i in range(1, max_container + 1):
                for client_i in range(1, max_clients + 1):

                    # start container
                    while len(containers) < container_i:
                        self._logger.info("Start container {} ...".format(len(containers) + 1))
                        container = Client(os.getenv("TEST_URL"), logger=self._logger,
                                           name="Container_{}".format(len(containers) + 1))
                        container.put({"event": "skillRegister", "data": {
                            "name": "skill_test"
                        }})
                        container.start()
                        containers.append(container)

                    # start client
                    while len(clients) < client_i:
                        self._logger.info("Start client {} ...".format(len(clients) + 1))
                        client = Client(os.getenv("TEST_URL"), logger=self._logger,
                                        name="Client_{}".format(len(clients) + 1))
                        client.start()
                        auth = client.auth()
                        clients.append(client)

                    # send request
                    self._logger.info(
                        "Send request with clients {} and containers {} ...".format(client_i, container_i))
                    for i, client in enumerate(clients):
                        for j, container in enumerate(containers):
                            for delay in [0, 25, 50]:  # ms
                                for message_i in range(1, max_messages + 1, 10):
                                    client_check(client)
                                    client.put({"event": 'skillRequest',
                                                "data": {'id': "stress_{}_{}_{}_{}".format(i, j, delay, message_i),
                                                         'name': "skill_test",
                                                         'data': {
                                                             'start': time.perf_counter(),
                                                             'client': i,
                                                             'delay': delay,
                                                             'message': message_i,
                                                         },
                                                         'config': {'return_stats': True}}})
                                    time.sleep(delay / 1000)

            self._logger.info("Check if there are open responses?")
            end = time.perf_counter() + 5
            while time.perf_counter() < end:
                for client in clients:
                    client_check(client)

        self._logger.info("Stop all clients and containers ...")
        for client in clients:
            client.stop()
        for container in containers:
            container.stop()

    def test_request_quota(self):
        """
        Check if quota is working
        :return:
        """
        self._logger.info("Start test request quota ...")
        self.client.clear()
        total_requests = 0
        for i in range(int(self._config['quota']['guest']['requests']) * 2):
            total_requests += 1
            self.client.put({'event': "authRequest", 'data': "test"})

        timeout = time.perf_counter() + 2
        messages = 0

        while time.perf_counter() < timeout:
            m = self.client.wait_for_event("authChallenge")
            if m:
                if 'event' in m and m['event'] == "authChallenge":
                    messages += 1

        self.assertEqual(int(self._config['quota']['guest']['requests']), messages)

    def test_delay(self):
        """
        Check if simulated delay is working
        :return:
        """
        self._logger.info("Start test delay ...")
        self.client.clear()
        self.client.put({"event": 'skillRequest', "data": {'id': "delay", 'name': "test_skill",
                                                           'config': {'min_delay': 1, "return_stats": True},  # 500ms
                                                           'data': time.perf_counter()}})

        self._logger.info("Sending request in between ...")
        time.sleep(0.01)
        self.client.put({"event": 'skillRequest', "data": {'id': "between", 'name': "test_skill",
                                                           'config': {"return_stats": True},
                                                           'data': time.perf_counter()}})

        message = self.client.wait_for_event("skillResults")['data']
        self._logger.debug("Main process received message: {}".format(message))
        self.assertEqual(message['id'], "between")

        message = self.client.wait_for_event("skillResults")['data']
        self._logger.debug("Main process received message: {}".format(message))
        self.assertEqual(message['id'], "delay")
        self.assertGreater(time.perf_counter() - message['data'], 1)

    def test_scrub(self):
        """
        Check if scrubbing is working
        :return:
        """
        self._logger.info("Start test scrub ...")
        # run scrub
        self._logger.info("Clean db")
        aql_query = """
            FOR doc IN tasks
            FILTER doc.request.id IN ["donated", "not_donated", "not_donated_without_key"]
            RETURN doc
        """
        cursor = self._db.sync_db.aql.execute(aql_query, count=True)
        for d in cursor:
            self._db.sync_db.delete_document(d)

        self.client.put({"event": 'skillRequest', "data":
            {'id': "donated", 'name': "test_skill", 'config': {'donate': True}, 'data': time.perf_counter()}})
        self.client.put({"event": 'skillRequest', "data":
            {'id': "not_donated", 'name': "test_skill", 'config': {'donate': False}, 'data': time.perf_counter()}})
        self.client.put({"event": 'skillRequest', "data":
            {'id': "not_donated_without_key", 'name': "test_skill", 'data': time.perf_counter()}})

        self.client.wait_for_event("skillResults")
        self.client.wait_for_event("skillResults")
        self.client.wait_for_event("skillResults")
        message1 = self.client.find_results("donated")
        self.assertEqual(message1['id'], "donated")
        message2 = self.client.find_results("not_donated")
        self.assertEqual(message2['id'], "not_donated")
        message3 = self.client.find_results("not_donated_without_key")
        self.assertEqual(message3['id'], "not_donated_without_key")

        aql_query = """
            FOR doc IN tasks
            FILTER doc.request.id IN ["donated", "not_donated", "not_donated_without_key"]
            RETURN doc
        """
        cursor = self._db.sync_db.aql.execute(aql_query, count=True)
        self.assertEqual(cursor.count(), 3)

        # run scrub
        time.sleep(2)
        self._logger.info("Starting scrubbing")
        scrub_config = {
            "scrub": {
                "enabled": True,
                "maxAge": 1,
                "interval": 1,
            },
            "cleanDbOnStart": False,
        }
        scrub_job(overwrite_config=scrub_config)

        cursor = self._db.sync_db.aql.execute(aql_query, count=True)
        return self.assertEqual(cursor.count(), 1)

    def test_auth(self):
        """
        Check authentication work
        :return:
        """
        self._logger.info("Start test auth ...")

        self._logger.info("Start container for auth")
        client = Client(logger=self._logger, url=os.getenv("TEST_URL"))
        client.start()
        auth = client.auth()
        client.stop()
        if auth:
            return self.assertEqual(auth['data']['role'], "admin")
        else:
            return self.fail("Auth failed")

    def test_roles(self):
        """
        Check if skills can be selected for specific roles
        :return:
        """
        self._logger.info("Start test roles ...")

        self._logger.info("Start container with user role")
        container = Client(os.getenv("TEST_URL"), logger=self._logger,
                           name="Container_Roles")
        container.put({"event": "skillRegister", "data": {
            "name": "skill_role_test", "roles": ["user"]
        }})
        container.start()

        # get skills
        client = Client(logger=self._logger, url=os.getenv("TEST_URL"))
        client.start()

        client.wait_for_event("skillUpdate")
        skills = [skill['name'] for skill in client.skills]

        self.assertNotIn("skill_role_test", skills)

        # authenticate as user
        client.auth(private_key_path=None)

        client.wait_for_event("skillUpdate")
        skills = [skill['name'] for skill in client.skills]

        self.assertIn("skill_role_test", skills)

        # authenticate as admin
        client.auth()
        client.wait_for_event("skillUpdate")
        skills = [skill['name'] for skill in client.skills]

        client.stop()
        container.stop()
        return self.assertIn("skill_role_test", skills)

    def test_job_quota(self):
        """
        Test if job quota is working
        """
        self._logger.info("Start test job quota ...")

        total_requests = 0
        for i in range(int(self._config['quota']['guest']['requests']) * 2):
            total_requests += 1
            self.client.put({"event": 'skillRequest', "data": {'id': "quota", 'name': "test_skill",
                                                               'config': {'min_delay': 2, "return_stats": True},
                                                               'data': {'start': time.perf_counter(), 'sleep': 1,
                                                                        'request': total_requests}}})

        timeout = time.time() + 5
        messages = 0
        job_errors = 0
        request_errors = 0
        while time.time() < timeout:
            m = self.client.check_queue()
            if m:
                self._logger.error(m)

                if m['event'] == 'skillResults' and m['data']['id'] == "quota":
                    self._logger.error("Received message: {}".format(m))
                    messages += 1
                if m['event'] == 'error' and m['data']['code'] == 101:
                    job_errors += 1
                if m['event'] == 'error' and m['data']['code'] == 100:
                    request_errors += 1

        self.assertLess(messages, total_requests)
        self.assertEqual(request_errors, total_requests - self._config['quota']['guest']['requests'])
        self.assertEqual(self._config['quota']['guest']['jobs'], messages)
        self.assertEqual(job_errors, total_requests - (
                self._config['quota']['guest']['requests'] + self._config['quota']['guest']['jobs']))

    def test_abort_unsupported(self):
        """
        Test if abort error without kill feature support
        :return:
        """
        self._logger.info("Start test abort unsupported ...")

        # with simulate (not finished) and kill feature disabled
        self.client.put({"event": 'skillRequest',
                         "data": {'id': "abort", 'name': "test_skill",
                                  'config': {'simulate': 10, 'min_delay': 10, "return_stats": True},
                                  'data': {'start': time.perf_counter()}}})
        time.sleep(1)

        self.client.put({"event": 'requestAbort', "data": {'id': "abort"}})

        result = self.client.wait_for_event("error")
        message = result['data']
        self.assertEqual(message['code'], 107)

    def test_abort_finished(self):
        """
        Test abort error with finished task
        :return:
        """
        self._logger.info("Start test abort finished ...")

        # add not skill with kill feature support
        self._container.put({"event": 'skillRegister', 'data': {"name": "test_skill_with_kill", "features": ['kill']}})
        self.client.wait_for_event("skillUpdate")
        self.assertTrue(self.client.check_skill("test_skill_with_kill"))

        # task already finished
        self.client.put({"event": 'skillRequest',
                         "data": {'id': "abort2", 'name': "test_skill_with_kill",
                                  'config': {"return_stats": True},
                                  'data': {'start': time.perf_counter()}}})

        time.sleep(1)

        self.client.put({"event": 'requestAbort', "data": {'id': "abort2"}})

        result = self.client.wait_for_event("error")
        message = result['data']
        self.assertEqual(message['code'], 105)

    def test_register_skill_multiple_times(self):
        """
        Test if skill can be registered multiple times
        :return:
        """
        self._logger.info("Start test register skill multiple times ...")
        containers = []
        for i in range(1, 3, 1):
            self._logger.info("Start container {} ...".format(len(containers) + 1))
            container = Client(os.getenv("TEST_URL"), logger=self._logger,
                               name="Container_{}".format(len(containers) + 1))
            container.start()
            container.put({"event": "skillRegister", "data": {
                "name": "multiple_skill_test", "config": {}
            }})
            containers.append(container)

        time.sleep(3)
        while self.client.check_queue():
            time.sleep(0.1)

        self.assertEqual(next(skill for skill in self.client.skills if skill['name'] == "multiple_skill_test")['nodes'],
                         2)

        container = Client(os.getenv("TEST_URL"), logger=self._logger, name="Container_{}".format(len(containers) + 1))
        container.put({"event": "skillRegister", "data": {
            "name": "multiple_skill_test", "anotherConfig": "fail"
        }})
        container.start()
        error = container.wait_for_event("error")
        self.assertEqual(error['data']['code'], 201)

        container.stop()
        for container in containers:
            container.stop()

    def test_abort_success(self):
        """
        Test abort success
        """
        self._logger.info("Start test abort success ...")

        # add not skill with kill feature support
        self._container.put({"event": 'skillRegister', 'data': {"name": "test_skill_with_kill", "features": ['kill']}})
        self.client.wait_for_event("skillUpdate")
        self.assertTrue(self.client.check_skill("test_skill_with_kill"))

        # task already finished
        self.client.put({"event": 'skillRequest',
                         "data": {'id': "abort3", 'name': "test_skill_with_kill",
                                  'config': {"return_stats": True},
                                  'data': {'sleep': 20, 'start': time.perf_counter()}}})

        time.sleep(1)

        self.client.put({"event": 'requestAbort', "data": {'id': "abort3"}})

        result = self.client.wait_for_event("error")
        message = result['data']

        self.assertEqual(message['code'], 109)

        result = self._container.wait_for_event("taskKill")
        self.assertIsNot(result, None)
        self.assertIsNot(result, False)

    def test_status_update(self):
        """
        Test if status updates are working
        :return:
        """
        self._logger.info("Start test status update ...")

        # clean container queue
        while self._container.check_queue():
            pass

        self._container.put({"event": 'skillRegister', 'data': {"name": "status_skill", "features": ['status']}})
        self.client.wait_for_event("skillUpdate")

        self.client.put({"event": 'skillRequest', "data": {'id': "status_update", 'name': "status_skill",
                                                           'config': {'min_delay': 2, "return_stats": True,
                                                                      "status": 1},
                                                           'data': {'start': time.perf_counter(), 'sleep': 10}}})

        # Send update
        time.sleep(1)
        task = self._container.wait_for_event("taskRequest")
        self._container.put(
            {"event": 'taskResults', "data": {'id': task['data']['id'], "status": "running", 'data': {'info': 'test'}}})

        result = self.client.wait_for_event("skillStatus")
        self.assertEqual(isinstance(result['data']['data'], list), True)
        self.assertEqual(result['data']['data'][0]['data']['info'], "test")

    def test_skill_config(self):
        """
        Test if config can be retrieved
        :return:
        """
        self._logger.info("Start test skill config ...")

        self.client.put({"event": 'skillGetConfig', "data": {'name': "test_skill"}})

        result = self.client.wait_for_event("skillConfig")
        self.assertEqual(result['data']['name'], "test_skill")

    def test_task_killer(self):
        """
        Test if task killer is working
        :return:
        """
        self._logger.info("Start test task killer ...")

        pass


if __name__ == '__main__':
    unittest.main()
