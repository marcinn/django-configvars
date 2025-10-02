Usage
=====

Precedence
----------

Values are resolved in this order:

1. environment variable
2. local settings module
3. default passed in code

Regular configuration values
----------------------------

.. code-block:: python

   from configvars import config

   DEBUG = config("DEBUG", False)
   ALLOWED_HOSTS = config("ALLOWED_HOSTS", "localhost").split(",")

Secret values
-------------

.. code-block:: python

   from configvars import secret

   DB_PASSWORD = secret("DB_PASSWORD", file_var="DB_PASSWORD_FILE")

Descriptions in dumps
---------------------

Both ``config()`` and ``secret()`` support ``desc=...`` for management command
output:

.. code-block:: python

   API_URL = config("API_URL", "https://example.com", desc="Base API URL")

Env prefixes
------------

Use ``initialize(env_prefix="APP_")`` to avoid name collisions:

.. code-block:: python

   from configvars import initialize, config

   initialize(env_prefix="APP_")
   API_KEY = config("API_KEY")

This resolves ``APP_API_KEY`` in the environment.

