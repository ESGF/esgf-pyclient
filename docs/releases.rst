Release Notes
=============

Release 0.1b1
-------------

This release marks the start of the 0.1 series which is considered beta-quality.  API changes in this series will be clearly marked in the documentation and backward-compatible releases will be maintained on pypi.

The 0.1b1 release includes integrated MyProxy logon support in the :mod:`pyesgf.logon` module.  This release also includes optimisations to the search system to avoid querying multiple shards when requesting the files from a dataset.

Release 0.1.1
-------------

This release will include wget script download support.

.. warning::
   The expected value of the *url* parameter to :meth:`SearchConnection()` has changed in this release. 
   Prior to v0.1.1 the *url* parameter expected the full URL of the
   search endpoint up to the query string.  This has now been changed
   to expect *url* to ommit the final endpoint name,
   e.g. ``http://pcmdi9.llnl.gov/esg-search/search`` should be changed
   to ``http://pcmdi9.llnl.gov/esg-search`` in client code.  The
   current implementation detects the presence of ``/search`` and
   corrects the URL to retain backward compatibility but this feature
   may not remain in future versions.

This release changes the call signature of :meth:`SearchConnection.send_query()` and introduces the additional methods :meth:`send_search()` and :meth:`send_wget()`.  When upgrading code to work with this new API simly:

 1. Change the *url* parameter to :meth:`SearchConnection()` to not include the ``/search`` suffix
 2. Change any occurance of :meth:`send_query()` to :meth:`send_search()`
