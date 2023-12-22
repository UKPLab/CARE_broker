import time
from collections import deque
import numpy as np


class Quota:
    """
    This class is used to limit the number of requests per second for a specific client.

    @author: Dennis Zyska
    """

    def __init__(self, max_len=100, interval=1):
        self.max_len = max_len
        self.queue = None
        self.interval = interval

        if max_len > 0:
            self.reset()

    def __call__(self, append=True):
        """
        Check if the quota is exceeded for a specific sid

        :param append: add current time to queue if quota is not exceeded
        :return:
        """
        if self.queue is None:
            return False

        if self.exceed():
            return True
        else:
            if append:
                self.queue.append(time.perf_counter())
            return False

    def exceed(self):
        """
        Check if the quota is exceeded for a specific sid

        :return: True if quota is exceeded
        """
        if len(self.queue) >= self.max_len:
            elapsed_time = time.perf_counter() - self.queue[0]
            if elapsed_time >= self.interval:
                self.queue.popleft()
                return False
            else:
                return True

    def reset(self):
        """
        Reset the quota
        """
        self.queue = deque(maxlen=self.max_len)
