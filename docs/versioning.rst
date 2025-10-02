Versioned Documentation
=======================

Publishing model
----------------

The GitHub Pages workflow builds documentation:

* from tags (release docs)
* from the development branch as ``dev`` (development docs)

This keeps release documentation immutable and allows a moving ``dev`` version.

URL layout
----------

Typical published URLs:

* ``https://marcinn.github.io/django-configvars/<tag>/``
* ``https://marcinn.github.io/django-configvars/dev/``

The site root contains a generated landing page with links to all built
versions.

Notes for old tags
------------------

If an old tag does not contain the ``docs/`` directory, the workflow skips it.
