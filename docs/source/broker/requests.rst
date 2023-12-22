Requests
========

Options
-------

In addition to the configuration options described in the :doc:`Skills <./skills/definition>` section,
the following options are available during runtime for each skill request.

Example:

.. code-block:: python

    sio.emit('skillRequest', {... config: {"return_stats": True} ...)

.. option:: return_stats

    This option is used to enable or disable the return of statistics from the broker. By default, this option is set to ``false``.

.. option:: min_delay

    This option is used to set the minimum delay between the skillRequest and skillResults. By default, this option is set to ``0``.

    .. note::

        This option slows down the answer of the broker. It is useful when you want to simulate a delay in the communication between the broker and the skill container.
        However, the requests are immediately transferred to the container, only the broker waits until the response is sent.

.. option:: donate

    This option marks the dataset as donated to allow permanent usage. By default, this option is set to ``false``.

.. option:: max_runtime

    This option is used to set the maximum runtime of a skill. By default, this option is set to ``0``.

.. options:: status

    This option can be activated to get status updates from the broker if available. By default, this option is set to ``false``.
    An integer value can be used to set the minimum delay between the status updates.
    This guarantees not receiving any message, if the skill sends nothing, there is nothing to send!

    .. warning::

        This will reduce the quota of the user. The quota is reduced by the number of status updates.

    .. note::

        The broker will only send status updates if the skill container implements the feature.
        If the container sends skill updates, but the time limit is reached,
        open status updates will sent to the user at the time the container sends new status updates.

.. option:: simulate

    If set to true, the task will be created but not send to a node. Note that the skill must exists!
    If an integer is given it is used to set the delay between the creation of the task and the sending the response.
    The response is the skill example output if set, otherwise an empty response is send.

