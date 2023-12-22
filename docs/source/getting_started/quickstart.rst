Quickstart Guide
=================

This guide will help you get started with the Broker.

| You can either install the Broker on your local machine or use the Broker as a service.
| For a complete installation, please follow the instructions in :doc:`Installation <./installation>`.

.. note::

    Please be aware that the Broker is a websocket API based on `Socket.IO <https://socket.io/>`_ and therefore requires a websocket client to connect to it.
    The API is not accessible through a RESTful interface!


Sequence Diagram
----------------

To give you a better understanding of the communication between the Broker, Skills and Clients, we provide a sequence diagram of the communication:

.. image:: ./sequence.drawio.svg
   :width: 80%
   :align: center

Usage
-----

To use the broker you can use any Socket.IO API:

- `Socket.IO Client Libraries for Javascript <https://socket.io/docs>`_
- `Socket.IO Client Libraries for Python <https://python-socketio.readthedocs.io/en/latest/>`_

Here we provide some basic example for the Javascript API:

.. code-block:: javascript

    const {io} = require("socket.io-client");
    const socket = io("<broker url>", {
        query: {token: "<see .env file>"},
        reconnection: true,
        autoConnect: true,
        timeout: 10000, //timeout between connection attempts
    });

    socket.on('connect', function() {
        console.log('Connected to NLP Broker');
        socket.emit('skillGetAll')
    });

    // Received skill updates from the broker
    socket.on('skillUpdate', function(data) {
        console.log("New skill updates: " + data);
        // get config of first skill
        socket.emit('skillGetConfig', {name: data[0]['name']});
    });

    // Receive skill config from the broker
    socket.on('skillConfig', function(data) {
        console.log("Skill config for {}: {}".format(data['name'], data));
    });

    socket.on('disconnect', function() {
        console.log('disconnected');
    });

.. role:: javascript(code)
   :language: javascript

To execute a skill just call:

.. code-block:: javascript

    socket.emit("skillRequest", {id: "<unique id>", name: "<skill name>", data: "<skill data>", config: {donate: true}});


.. note::

    For authentication see :doc:`Authentication <../broker/authentication>`.

.. tip::

    Further examples (jupyter notebooks) can be found in the ``examples`` folder.