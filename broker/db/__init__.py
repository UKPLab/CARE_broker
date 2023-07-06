import time


def results(job):
    """Return the job result of an arango db async operation.
    """
    while job.status() == "pending":
        time.sleep(0.01)

    return job.result()
