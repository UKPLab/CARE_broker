Database
========

As a database we use `ArangoDB <https://www.arangodb.com>`_.
ArangoDB is a multi-model database with flexible data models for documents, graphs, and key-values.

In development mode the database can be accessed via the web interface at http://localhost:8529.

See https://docs.python-arango.com/en/main/ for more information on how to use the Python driver.

Scrubbing
---------

The database is scrubbed on every start of the application and in regular intervals.
The intervals can be configured in the .env file by setting the environment variable `SCRUB_INTERVAL`.

Currently the following collections are scrubbed:

- `task`: All tasks that are older as the environment variable `SCRUB_MAX_AGE` and don't have the option :doc:`donate <../skills/requests>` are deleted.

.. tip::

    You can also start the scrubbing manually by running the following command: ``make scrub``