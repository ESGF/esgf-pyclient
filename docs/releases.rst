Release Notes
=============

Release 0.1.8
-------------

This release includes the following changes:

 1. The tests have been updated and various fixes made to make them match the up-to-date ESGF Search API.
 2. Following problems with the search being slow in certain scenarios an extra call to the Search service 
    was made optional through the :meth:`SearchContext.search()` method. If you send the argument and value
    of `ignore_facet_check=True` then this hidden call to the service will be avoided. This typically saves
    2 seconds of wait time which can be very important in some iterative search scenarios.
 3. The :meth:`SearchContext.search()` method was also extended so that the argument `batch_size` could be
    directly sent to it in order to manage how the calls to the API would be separated out into batches. This
    does not affect the final result but may affect the speed of the response. The batch size can also be set
    as a default in the :mod:`pyesgf.search.consts` module.
 4. Searches at the file-level now return a `gridftp_url` property along with other existing properties such
    as `download_url`. 

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
