.. _installation:

************
Installation
************

Install from PyPI
=================

.. code-block:: console

  $ pip install esgf-pyclient

Install from Anaconda
=====================

.. image:: https://anaconda.org/conda-forge/esgf-pyclient/badges/installer/conda.svg
   :target: https://anaconda.org/conda-forge/esgf-pyclient
   :alt: Ananconda Install

.. image:: https://anaconda.org/conda-forge/esgf-pyclient/badges/version.svg
   :target: https://anaconda.org/conda-forge/esgf-pyclient
   :alt: Anaconda Version

.. image:: https://anaconda.org/conda-forge/esgf-pyclient/badges/downloads.svg
   :target: https://anaconda.org/conda-forge/esgf-pyclient
   :alt: Anaconda Downloads

.. code-block:: console

   $ conda install -c conda-forge esgf-pyclient

Install from GitHub
===================

Get esgf-pyclient source from GitHub_:

.. code-block:: console

   $ git clone https://github.com/ESGF/esgf-pyclient.git
   $ cd esgf-pyclient

Optionally create Conda_ environment named *esgf-pyclient*:

.. code-block:: console

   $ conda env create -f environment.yml
   $ conda activate esgf-pyclient

Install esgf-pyclient:

.. code-block:: console

   $ pip install -e .
   OR
   $ make install

For development you can use this command:

.. code-block:: console

  $ pip install -e .[dev]
  OR
  $ make develop

.. _GitHub: https://github.com/ESGF/esgf-pyclient
.. _Conda: https://conda.io/en/latest/
