Features
========

Skill can have special features, functionality that are implemented by the container itself.
The following features are supported:

.. option:: kill (alternative: abort)

    The container implemented the kill feature. This means that the container can kill the skill by itself.
    If activated the broker can send a kill message ``taskKill``  to the container.
    The user can also send a abort message for the request ``requestAbort``.

.. option:: task

    The container implemented the task information feature. This means that the container can provide additional information about the task status.
    If activated the broker can send a task message ``task``  to the container.

.. option:: status

    The container implemented the status feature. This means that the container can provide additional information about the skill status.
    If activated the broker can send intermediate status messages about the skill to the container.

    .. note::

        To send a status message to the broker, add a ``status`` key in the message.
        To finish the task, send a message without the ``status`` key, an empty ``status`` or ``finished`` as value.
        To ensure that the client receives the messages, the config "status" must be set to "true" in each request (see :doc:`Requests <../broker/requests>` for more information).




