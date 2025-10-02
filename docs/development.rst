Development
===========

Run docs locally
----------------

Install docs dependencies:

.. code-block:: bash

   python -m pip install -r docs/requirements.txt

Build HTML docs:

.. code-block:: bash

   make -C docs html

Output is written to ``docs/_build/html``.

Release workflow
----------------

The repository includes a GitHub Actions workflow that:

* rebuilds all tagged documentation versions
* builds ``dev`` from the development branch
* publishes the combined site to GitHub Pages

This is designed so published release docs come from tagged code, not from the
current default branch.
