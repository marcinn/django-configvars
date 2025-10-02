Installation
============

Package install
---------------

Install from PyPI (or your preferred source):

.. code-block:: bash

   pip install django-configvars

Basic Django setup
------------------

Add ``configvars`` to ``INSTALLED_APPS``:

.. code-block:: python

   INSTALLED_APPS = [
       # ...
       "configvars",
       # ...
   ]

Optional initialization
-----------------------

If you want a custom local settings module path or env prefix:

.. code-block:: python

   from configvars import initialize

   initialize(
       local_settings_module="myproject.local",
       env_prefix="APP_",
   )

If you do not call ``initialize()``, ``django-configvars`` tries to infer the
local module from ``DJANGO_SETTINGS_MODULE`` and uses no prefix.
