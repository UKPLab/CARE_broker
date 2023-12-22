import asyncio
import threading
import time
from datetime import datetime
from datetime import timedelta

from broker.db.collection import Collection
from broker.db.utils import results


class Tasks(Collection):
    """
    Task Collection

    @author: Dennis Zyska
    """

    def __init__(self, db, adb, config, socketio):
        super().__init__("tasks", db, adb, config, socketio)
        self.quotas = {}

        self.index = results(self.collection.add_hash_index(fields=['sid'], name='sid_index', unique=False))
        self.index = results(self.collection.add_hash_index(fields=['connected'], name='connected_index', unique=False))

        # start scrub task
        scrub_thread = threading.Thread(target=self.cron)
        scrub_thread.daemon = True
        scrub_thread.start()

    def create(self, sid, node, payload, parent=None):
        """
        Create a new task

        :param sid: sender id from request client
        :param node: node id send request to
        :param payload: task payload
        :param parent: parent task id
        :return:
        """
        # is max_runtime set?
        max_runtime = 0
        if "config" in payload and 'max_runtime' in payload['config']:
            max_runtime = payload['config']['max_runtime']
        if self.config['taskKiller']['enabled']:
            max_duration = self.config['taskKiller']['maxDuration']
            if max_runtime > max_duration:
                max_runtime = max_duration

        # is simulation set?
        if "config" in payload and 'simulate' in payload['config']:
            node_key = None
        else:
            node_key = node['_key']

        new_task = results(self.collection.insert({
            "rid": sid,  # request id
            "nid": node['sid'],  # node id
            "skill": node_key,  # node key
            "request": payload,
            "status": "created",
            "parent": parent,
            "max_runtime": (datetime.now() + timedelta(
                seconds=max_runtime)).isoformat() if max_runtime > 0 else "9999-12-31T23:59:59.000000",
            "start_timer": time.perf_counter(),
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat(),
        }))

        if "config" in payload and 'simulate' in payload['config']:
            if "output" in node['config'] and "example" in node['config']['output']:
                result = node['config']['output']['example']
            else:
                result = {}
            self.update(new_task['_key'], 0, result)
            return 0
        else:
            return int(new_task['_key'])

    def update(self, key, node, data):
        """
        Update task by key
        :param key: key of task
        :param node: node the result came from
        :param data: results of task
        :param error: error occurred
        """
        task = self.get(key)
        if task is None:
            self.socketio.emit("error", {'id': key, 'code': 108}, room=node)
            return

        # if simulate task has set an integer value, wait for this time
        if "config" in task['request'] and 'simulate' in task['request']['config']:
            if isinstance(task['request']['config']['simulate'], int):
                time.sleep(task['request']['config']['simulate'])

        if 'error' in data:
            task['status'] = 'error'
            task['error'] = data['error']
            task['updated'] = datetime.now().isoformat()
            self.collection.update(task)
            self.socketio.emit("error", {'id': key, 'code': 112, 'error': data['error']}, room=task['rid'])
            return

        if ('status' in data
                and data['status'] != 'finished'
                and data['status'] != ''):

            task['status'] = data['status']
            task['updated'] = datetime.now().isoformat()
            if 'updates' not in task:
                task['updates'] = []
            task['updates'].append({
                'status': data['status'],
                'updated': task['updated'],
                'notSent': True,
                'data': data['data'] if isinstance(data, dict) and 'data' in data.keys() else {}
            })

            # send status update to client
            if "config" in task['request'] and 'status' in task['request']['config']:
                if (isinstance(task['request']['config']['status'], bool)
                        and task['request']['config']['status']):
                    updates = [x for x in task['updates'] if x['notSent']]
                else:
                    sent_before = datetime.now() - timedelta(seconds=task['request']['config']['status'])
                    updates = [x for x in task['updates'] if
                               x['notSent'] and datetime.fromisoformat(x['updated']) > sent_before]

                # send status update to client
                if not self.db.clients.quota(task['rid'], append=True):
                    for update in updates:
                        del (update['notSent'])

                    output = {
                        'id': task['request']['id'],
                        'clientId': task['request']['clientId'] if 'clientId' in task['request'] else None,
                        'data': updates
                    }
                    # sending status update to client
                    self.socketio.emit("skillStatus", output, room=task['rid'])

            self.collection.update(task)

        else:
            task['end_timer'] = time.perf_counter()
            task["duration"] = task['end_timer'] - task["start_timer"]
            task["result"] = data
            task['status'] = 'finished'
            task["fid"] = node  # finish id
            self.collection.update(task)

            # update job quota
            self.db.clients.quotas[task['rid']]['jobs'].remove(task['_key'])

            output = {
                'id': task['request']['id'],
                'clientId': task['request']['clientId'] if 'clientId' in task['request'] else None,
                'data': data['data'] if isinstance(data, dict) and 'data' in data.keys() else {}
            }
            if "config" in task['request'] and 'return_stats' in task['request']['config']:
                output['stats'] = {
                    'duration': task["duration"],
                    'host': node,
                }
                if 'stats' in data:
                    output['stats']['result'] = data['stats']

            if "config" in task['request'] and 'min_delay' in task['request']['config']:
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:  # 'RuntimeError: There is no current event loop...'
                    loop = None

                if loop and loop.is_running():
                    # https://docs.python.org/3/library/asyncio-task.html#task-object
                    tsk = loop.create_task(
                        asyncio.sleep(
                            task['request']['config']['min_delay'] - (time.perf_counter() - task["start_timer"])))
                    tsk.add_done_callback(
                        lambda t: self.send_results(task['rid'], output))
                else:
                    asyncio.run(
                        asyncio.sleep(
                            task['request']['config']['min_delay'] - (time.perf_counter() - task["start_timer"])))
                    self.send_results(task['rid'], output)
            else:
                self.send_results(task['rid'], output)

            return {
                "rid": task["rid"],
                "output": output,
            }

    def cron(self):
        """
        Cronjob for cleaning up tasks
        """
        # arango.exceptions.AQLQueryExecuteError: [HTTP 400][ERR 600] VPackError error: Expecting digit
        # or arango.exceptions.AsyncJobStatusError: [HTTP 404][ERR 404] job 258578 not found
        return False

        while self.config['taskKiller']['enabled']:
            aql_query = "FOR doc IN @@collection " \
                        "FILTER (doc.status == 'running' OR doc.status == 'created') " \
                        "RETURN doc"
            # FILTER doc.status == 'running' or doc.status == 'created'
            # FILTER doc.max_runtime < DATE_NOW()
            cursor = self.db.sync_db.aql.execute(aql_query, bind_vars={"@collection": self.name}, count=True)
            for task in cursor:
                self.abort(task)
            time.sleep(self.config['taskKiller']['interval'])

    def terminate_by_disconnect(self, sid):
        """
        Abort all tasks because one client is disconnected
        :param sid: session id of user
        :return:
        """
        aql_query = """
                FOR doc IN @@collection
                FILTER (doc.status == "running" OR doc.status == "created")
                AND (doc.nid == @sid OR doc.rid == @sid)
                RETURN doc
            """
        cursor = results(self._sysdb.aql.execute(aql_query, bind_vars=
        {
            "@collection": self.name,
            "sid": sid
        }))
        for task in cursor:
            if task['nid'] == sid:
                # node disconnected, is there another node?
                node = self.db.skills.get_node(task['rid'], task['request']["name"])
                if node is None:
                    self.abort(task, reason="node disconnected", kill=False, error=103)
                else:
                    # start task on other node
                    task = self.db.tasks.create(task["rid"], node, task['request'], parent=task['_key'])
                    self.socketio.emit("taskRequest", {'id': task['_key'], 'data': task['request']['data']}, room=node)
                    self.abort(task, reason="node disconnected", kill=False, error=104)
            else:
                # client disconnected
                if self.db.skills.check_feature(task['skill'], feature=['kill', 'abort'], check_all=False):
                    self.abort(task, reason="client disconnected", kill=True, error=False)

    def abort_by_user(self, id, sid):
        """
        Abort task by user
        :param id: task id
        :param sid: session id of user
        :return:
        """
        cursor = results(self._sysdb.aql.execute("""
            FOR doc IN @@collection
            FILTER doc.rid == @rid 
            AND doc.request.id == @id
            LIMIT 1
            RETURN doc
        """, bind_vars={
            "@collection": self.name,
            "rid": sid,
            "id": id
        }, count=True))
        if cursor.count() > 0:
            task = cursor.next()
            if self.db.skills.check_feature(task['skill'], feature=['kill', 'abort'], check_all=False):
                if task['status'] == "finished" or task['status'] == "aborted":
                    self.socketio.emit("error", {"code": 105}, room=sid)
                else:
                    self.abort(task, error=109)
                return True
            else:
                self.socketio.emit("error", {"code": 107}, room=sid)
            return True
        return False

    def abort(self, task, reason="", kill=True, error=110):
        """
        Abort task by key
        :param task: task to abort
        :param reason: reason for abort
        :param kill: send kill emit to node
        :param error: send error code to client
        :return:
        """
        if kill:
            self.socketio.emit("taskKill", {"id": task['_key']}, room=task['nid'])

        # update job quota
        self.db.clients.quotas[task['rid']]['jobs'].remove(task['_key'])

        # update task
        task['status'] = "aborted"
        task['reason'] = reason
        task['updated'] = datetime.now().isoformat()
        self.collection.update(task)

        # send results to client
        if error:
            self.socketio.emit("error", {"code": error}, room=task['rid'])

    def send_results(self, rid, payload):
        """
        Send results to request client
        :param rid: session id of request client
        :param payload: data to send
        :return:
        """
        self.socketio.emit("skillResults", payload, room=rid)

    def clean(self):
        """
        Clean up tasks on start
        """
        cleaned = results(self.collection.update_match({"connected": True}, {"connected": False, "cleaned": True}))
        self.logger.info("Cleaned up {} tasks".format(cleaned))

    def scrub(self, run_forever=True):
        """
        Regular task for cleaning db - delete old entries
        :param run_forever: run forever as called in thread
        :param max_age: overwrite max age threshold and force scrub
        :return:
        """
        once = True
        while run_forever or once:
            aql_query = """
                FOR doc IN tasks
                FILTER doc.status != 'running' && doc.status != 'created'
                FILTER doc.updated < @timestamp
                FILTER (NOT HAS(doc.request.config, 'donate') || doc.request.config.donate == false)
                RETURN doc
            """
            if self.config['scrub']['enabled'] and self.config['scrub']['maxAge'] > 0:
                timestamp_threshold = datetime.now() - timedelta(seconds=self.config['scrub']['maxAge'])
                query_params = {'timestamp': timestamp_threshold.isoformat()}
                cursor = results(self._sysdb.aql.execute(aql_query, bind_vars=query_params))
                for entry in cursor:
                    print("Delete by scrub: Task {}".format(entry['_key']))
                    self.collection.delete(entry['_key'])
            if run_forever:
                time.sleep(self.config['scrub']['interval'])
            once = False
