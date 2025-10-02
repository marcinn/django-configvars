API Reference
=============

Module-level helpers
--------------------

``initialize(local_settings_module=None, env_prefix=None)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Initialize the shared config registry.

* ``local_settings_module``: dotted path to the local settings module
* ``env_prefix``: prefix for environment variable lookup (for example ``APP_``)

``config(var, default=None, desc=None)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Resolve a regular config value and register it for the management command.

``secret(var=None, default=None, desc=None, file_var=None, allow_multiline=False)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Resolve a secret value and register it as masked.

Parameters:

* ``var``: literal secret variable name (for example ``DB_PASSWORD``)
* ``file_var``: companion variable name containing a secret file path
* ``default``: fallback value if neither env nor local is set
* ``desc``: optional human-readable description
* ``allow_multiline``: allow multiline content when reading from ``file_var``

``get_config_variables()``
~~~~~~~~~~~~~~~~~~~~~~~~~~

Return the internal registry of declared config variables (used by the
management command).

Casting helpers
---------------

``as_bool(value)``
~~~~~~~~~~~~~~~~~~

Convert common string values to booleans.

``as_list(value, separator=",")``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Split comma-separated strings into lists (or pass lists/tuples through).

Autodoc reference
-----------------

.. automodule:: configvars
   :members: initialize, config, secret, get_config_variables, as_bool, as_list
   :undoc-members:
