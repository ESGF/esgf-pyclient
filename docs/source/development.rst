***********
Development
***********

Get Started!
============

Check out code from the esgf-pyclient GitHub repo and start the installation:

.. code-block:: console

  $ git clone https://github.com/ESGF/esgf-pyclient.git
  $ cd esgf-pyclient
  $ conda env create -f environment.yml
  $ pip install -e .[dev]

When you're done making changes, check that your changes pass `flake8` and the tests:

.. code-block:: console

  $ flake8
  $ pytest

Or use the Makefile:

.. code-block:: console

  $ make lint
  $ make test  # skip slow tests
  $ make test-all

Write Documentation
===================

You can find the documentation in the `docs/source` folder. To generate the Sphinx
documentation locally you can use the `Makefile`:

.. code-block:: console

  $ make docs

Bump a new version
===================

Make a new version of esgf-pyclient in the following steps:

* Make sure everything is commit to GitHub.
* Update ``CHANGES.rst`` with the next version.
* Dry Run: ``bumpversion --dry-run --verbose --new-version 0.3.1 patch``
* Do it: ``bumpversion --new-version 0.3.1 patch``
* ... or: ``bumpversion --new-version 0.4.0 minor``
* Push it: ``git push --tags``

See the bumpversion_ documentation for details.

.. _bumpversion: https://pypi.org/project/bumpversion/
