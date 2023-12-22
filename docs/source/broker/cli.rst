Command Line Interface
======================

With the client it is possible to work with the broker during the command line.
You can run it by simple execute ``python3 cli.py --help``.

For using the client you need to install the python environment. We recommend to use conda for this
(see `Miniconda Install <https://docs.conda.io/projects/miniconda/en/latest/miniconda-install.html>`_).
After installing conda, you can use the following command to set up the environment:

.. code-block:: bash

    conda env create -f environment.yml
    conda env update --file environment.yaml --name nlp_api --prune     # for updating the environment
    conda activate nlp_api

.. tip::

    # TODO add docker instructions
    If you run on docker use ``docker exec -it <container_name> python3 broker/app.py --help``.

The following parameters are available:

* ``-h`` or ``--help``: Show the help message.
* ``broker``: Submenu for broker commands.
* ``skills``: Submenu for skill commands.

Broker
------

This will be in the future the main interface for the broker.
Currently is is possible to use it with ``python3 broker/app.py --help``.

* ``-h`` or ``--help``: Show the help message.
* ``scrub``: Start :doc:`scrub <db>` job for the database.
* ``init``: Set the current system admins' public key.
* ``assign``: Assign a role to a user (with the user's public key).

.. warning::

    The commands are currently only available with ``python3 broker/app.py --help``.


Skills
------

With the skills submenu you can publish several integrated models to the broker (see :doc:`available models </models/models>` for a list). The following commands are available:

* ``-h`` or ``--help``: Show the help message.
* ``list``: List all available skills.
* ``build``: Build the container for the skills
* ``run``: Run the container for the skills
* ``stop``: Stop the container for the skills

.. tip::

    There are many extra parameter available, use ``-h`` to see all available parameters for each command.