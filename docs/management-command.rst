Management Command
==================

Command name
------------

.. code-block:: bash

   python manage.py configvars

The command prints registered config variables from the settings module.

Examples
--------

Default output:

.. code-block:: text

   DB_NAME = 'example'
   DB_USER = 'postgres'
   DB_PASSWORD = '*****'
   DB_HOST = 'localhost'
   DB_PORT = 5432

Options
-------

``--changed``
~~~~~~~~~~~~~

Show only values changed from defaults.

.. code-block:: bash

   python manage.py configvars --changed

``--defaults``
~~~~~~~~~~~~~~

Show defaults instead of current resolved values.

.. code-block:: bash

   python manage.py configvars --defaults

``--comments``
~~~~~~~~~~~~~~

Show descriptions added with ``desc=...``.

.. code-block:: bash

   python manage.py configvars --comments

Notes
-----

* Secret values are masked as ``"*****"`` when set.
* Unset secrets are shown as ``None``.

