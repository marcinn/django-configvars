Quickstart
==========

Declare settings in ``settings.py``
-----------------------------------

.. code-block:: python

   from configvars import config, secret

   SOME_API_KEY = config("SOME_API_KEY", "default_api_key")
   SOME_API_SECRET = secret("SOME_API_SECRET")

Local overrides
---------------

Create ``local.py`` next to your Django settings module:

.. code-block:: python

   SOME_API_KEY = "LOCAL_API_KEY"
   SOME_API_SECRET = "LOCAL_SECRET"

Environment overrides
---------------------

.. code-block:: bash

   SOME_API_KEY="ENV_API_KEY" python manage.py configvars

Secrets with files (Swarm / Portainer)
--------------------------------------

.. code-block:: python

   DB_PASSWORD = secret("DB_PASSWORD", file_var="DB_PASSWORD_FILE")

.. code-block:: bash

   # literal
   APP_DB_PASSWORD="plain-password"

   # file-based secret
   APP_DB_PASSWORD_FILE="/run/secrets/db_password"

