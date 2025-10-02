Development
===========

Run docs locally
----------------

Install docs dependencies:

.. code-block:: bash

   make docs-setup

Build HTML docs:

.. code-block:: bash

   make docs

Output is written to ``docs/_build/html``.

Build multiversion docs locally (tags):

.. code-block:: bash

   make docs-multiversion

Release workflow
----------------

The repository includes a GitHub Actions workflow that runs
``sphinx-multiversion`` and publishes the generated site to GitHub Pages.

Release documentation comes from tags. The published site also contains a
``latest/`` alias pointing to the newest release.
