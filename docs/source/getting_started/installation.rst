.. _installation:
Installation
============
This section describes how to install the Broker.

Prerequisites
*************

Docker is required to build the containers.
Please install them according to the official documentation:

* `Docker <https://docs.docker.com/engine/installation/>`_

or install Docker Desktop:

* `Docker Desktop for Windows <https://docs.docker.com/docker-for-windows/install/>`_
* `Docker Desktop for Mac <https://docs.docker.com/desktop/install/mac-install/>`_
* `Docker Desktop for Linux <https://docs.docker.com/desktop/install/linux-install/>`_

Also make sure that you have GNU's ``make`` installed on your system.

.. note::

    On Windows, you can use the ``make`` command with the `GNU Make for Windows <http://gnuwin32.sourceforge.net/packages/make.htm>`_ package.
    On newer windows systems, simply use ``winget install GnuWin32.Make`` and make it executable with ``set PATH=%PATH%;C:/Program Files (x86)/GnuWin32/bin``.

.. note::

    On Ubuntu, you need to install the docker compose plugin with ``sudo update && sudo apt-get install docker-compose-plugin``.


For installing the requirements of the command line interface see section :doc:`CLI </broker/client>`.

Build
*****

To build the broker, change the .env.main file to your requirements and
run the following command in the root directory of the project:

.. code-block:: bash

    make ENV=main build

This will build all docker image for the NLP server.

.. warning::::

    The ``ENV`` variable must be set to ``main`` or ``dev``, otherwise connection to the DB is not possible!
    The ``dev`` environment is used for development purpose only.

Development
***********

To start the broker in development mode, run the following command in the root directory of the project:

.. code-block:: bash

    make docker
    make broker

See section :doc:`Development </broker/development>` for more information.



