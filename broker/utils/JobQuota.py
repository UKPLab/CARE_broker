import numpy as np

from broker.utils.Quota import Quota


class JobQuota(Quota):
    """
    Job quota for a specific client

    @author: Dennis Zyska
    """

    def __call__(self, append=None):
        """
        Check if the quota is exceeded for a specific sid

        :param append: set job key to queue if quota is not exceeded
        :return:
        """
        if self.queue is None:
            return False

        if self.exceed():
            return True
        else:
            if append:
                self.queue[(self.queue == 0).argmax(axis=0)] = int(append)
            return False

    def exceed(self):
        """
        Check if the quota is exceeded for a specific sid

        :return: True if quota is exceeded
        """
        if (self.queue == 0).any():
            return False
        else:
            return True

    def remove(self, task_id):
        """
        Remove a job from the quota

        :param task_id: task id
        """
        if self.queue is not None:
            self.queue[self.queue == int(task_id)] = 0

    def append(self, task_id):
        """
        Append a job to the quota
        :param task_id:
        :return:
        """
        if self.queue is not None:
            self.queue[(self.queue != 0).argmax(axis=0)] = task_id

    def update(self, reserved_id, task_id):
        """
        Update the quota with a reserved id
        :param reserved_id:
        :param task_id:
        :return:
        """
        if self.queue is not None:
            self.queue[(self.queue == reserved_id).argmax(axis=0)] = task_id

    def reset(self):
        """
        Reset the quota
        """
        self.queue = np.zeros(self.max_len, dtype=int)
