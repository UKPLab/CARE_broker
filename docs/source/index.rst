Welcome to the Broker's documentation!
======================================

The Broker should provide a simple interface to a variety of tools and models.
It is designed to be used by the Broker API based on websockets to keep the inference times as low as possible.

The goal is to give as many clients as possible access to models at the same time.
The models should therefore connect to the Broker independently when available and be available from that point on.

.. note::

   It cannot be guaranteed that all models will be available at all times.
   The Broker does not start any models and if the models crash it is the responsibility of the models container
   to restart the model and reconnect to the Broker on their own.
   We also implemented a quota system to prevent a single client from using all available resources (see ::doc:`Config </broker/config>`).

| Tools and models are registered as so called :doc:`Skills <./skills/definition>`, each having a specific task.
| See :doc:`Quickstart <./getting_started/quickstart>` for a quick introduction to the Broker.

The broker is developed as part of the `CARE project <https://github.com/UKPLab/CARE>`_ at the `UKP Lab <https://www.informatik.tu-darmstadt.de/ukp/ukp_home/index.en.jsp>`_ at the `TU Darmstadt <https://www.tu-darmstadt.de/index.en.jsp>`_.


.. toctree::
   :maxdepth: 1
   :caption: Getting Started

   getting_started/quickstart
   getting_started/installation

.. toctree::
   :maxdepth: 1
   :caption: Broker

   broker/config
   broker/authentication
   broker/cli
   broker/requests
   broker/development
   broker/db



.. toctree::
   :maxdepth: 1
   :caption: Skills

   skills/definition
   skills/features
   skills/skill_definition_file
   skills/examples

.. toctree::
   :maxdepth: 1
   :caption: Models

   models/example
   models/models


