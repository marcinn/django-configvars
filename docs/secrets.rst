Handling Secrets
================

Overview
--------

``secret()`` resolves values from environment / local / default like
``config()``, but it masks configured values in ``manage.py configvars`` output.

Recommended pattern
-------------------

Use a literal variable plus optional ``*_FILE`` companion:

.. code-block:: python

   DB_PASSWORD = secret("DB_PASSWORD", file_var="DB_PASSWORD_FILE")

Runtime behavior
----------------

* If only ``DB_PASSWORD`` is set, the literal value is used.
* If only ``DB_PASSWORD_FILE`` is set, the file content is read.
* If both are set, ``ImproperlyConfigured`` is raised.
* If neither is set, the function falls back to local/default.

Security behavior
-----------------

``secret()`` no longer guesses that a literal value is a file path. File reads
only happen when ``file_var=...`` is passed explicitly.

This avoids accidental reads of unrelated files when an environment value
happens to look like an existing path.

File validation for ``file_var``
--------------------------------

By default:

* the file must exist
* the file must not exceed ``configvars.MAX_SECRET_FILE_SIZE``
* the file must be single-line

For multiline secrets (for example PEM blocks), enable it explicitly:

.. code-block:: python

   TLS_PRIVATE_KEY = secret(
       "TLS_PRIVATE_KEY",
       file_var="TLS_PRIVATE_KEY_FILE",
       allow_multiline=True,
   )

CLI masking
-----------

Configured secrets are masked in ``manage.py configvars`` output:

.. code-block:: text

   DB_PASSWORD = '*****'

Unset or empty values are still shown as ``None`` / ``''`` to avoid implying a
value exists when it does not.

