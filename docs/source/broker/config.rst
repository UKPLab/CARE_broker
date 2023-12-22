Configuration
=============

To adapt the broker's behavior to your needs, you can also adapt the ``config.yaml`` file in the broker's root directory.

The following options are available:

.. option:: quota

    There are several options to configure the quota system. The options are applied to each role (see :doc:`Authentication <./authentication>` individually.

    For each role, you can specify the following options:

    .. option:: jobs

        The maximum of concurrent jobs. If ``0``, no limit is applied.

    .. option:: requests

        The maximum number of requests per ``quotaInterval`` seconds. If ``0``, no limit is applied.

    .. option:: results

        The maximum number of results can be sent by a skill per ``quotaInterval`` seconds. If ``0``, no limit is applied.

.. option:: quotaInterval

    Period in seconds for which the quota should apply. Default is ``1`` second.

.. option:: scrub

    The database can be scrubbed automatically. This means that all data older than a certain time is deleted (not donated data!).
    This is useful to keep the database small and fast.
    The following options are available:

    .. option:: enabled

        If ``true``, the scrubbing is enabled.

    .. option:: interval

        The interval in seconds in which the scrubbing is performed.

    .. option:: maxAge

        The maximum age of data in the database in seconds. All data older than this value is deleted (expect donated data).
        If set to ``0``, no data is deleted.

.. option:: taskKiller

    The task killer is a mechanism to kill tasks that are running too long. This is useful to prevent a skill from blocking the whole system.

    .. warning::

        Especially the job quota is highly affected by this! If a task is running forever, the job quota is not freed.

    The following options are available:

    .. option:: enabled

        If ``true``, the task killer is enabled.

    .. option:: interval

        The interval in seconds in which the task killer is performed.

    .. option:: maxDuration

        The maximum age of a task in seconds.
        If a task is running longer than this value, a kill signal will be sent to the node (if node support it).
        and the client will be notified that the task failed.

.. option:: cleanDbOnStart

    Clean the database on start. This means that not closed connection (e.g., skills, clients) are set to disconnected.
