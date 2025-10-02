Overview
========

What it does
------------

`django-configvars` helps declare configuration values in ``settings.py`` and
resolve them from:

* environment variables
* a local settings module (by default ``<project>.local``)
* hard-coded defaults

This keeps settings explicit in code while allowing per-environment overrides.

Why use ``secret()``
--------------------

``secret()`` resolves values like ``config()``, but it marks them as sensitive
in the registry used by ``manage.py configvars`` so they are masked in output.

With file-based secret support, you can also read secrets from ``*_FILE``
variables (for Docker Swarm / Portainer style deployments).

Core concepts
-------------

* ``initialize(...)``: configure local settings module path and env prefix
* ``config(...)``: regular value, visible in config dump
* ``secret(...)``: secret value, masked in config dump
* ``get_config_variables()``: introspection used by the management command

