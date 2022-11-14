**********
Quickstart
**********

.. code-block:: console

  $ conda create -n esgf-pyclient -c conda-forge esgf-pyclient
  $ conda activate esgf-pyclient

Once installed you import the package as the name ``pyesgf``:

.. code-block:: python

  from pyesgf.search import SearchConnection
  conn = SearchConnection('http://esgf.ceda.ac.uk/esg-search',
                           distrib=True)
  ctx = conn.new_context(project='CMIP5', query='humidity')
  ctx.hit_count

See the :ref:`examples`.
