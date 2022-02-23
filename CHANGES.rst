Release Notes
=============

0.3.1 (2022-02-24)
------------------

- Fix #75: ignore_facet_check search option appears to be broken. (#79)
- Fix #74: Is there a way to search the entire ESGF? (#79)
- Fix #78: Updates for requests_cache API (#68).
- Add warnings when default facets=* used on distributed search (#77).
- Improve ignore_facet_check search argument (#76).
- Improvements to tests (#73).

0.3.0 (2021-02-08)
------------------

- Added test for batch size (#66).
- Test notebooks (#65).
- Replaced Travis CI by GitHub actions CI (#64).
- Return globus urls in search (#63).
- Fixed build of Search API (#61).
- Remove unused code (#49).
- Cleaned up tests (#45).
- Using ``webob.multidict`` (#43).
- Cleaned up docs (#39).
- Marked slow tests (#38).
- Added notebook examples (#37, #46, #48).
- Fixed the usage of the ``input()`` method in ``logon.py`` (#36).
- Skip Python 2.x (#35).

0.2.2 (2019-07-19)
------------------

- Fixed test suite (#33)
- Added badges for RTD and Travis CI to Readme.

0.2.1 (2018-03-14)
------------------

This release includes the following features:

- The library now supports **Python 3**.
- ``verify`` option in ``LogonManager`` has been added.
- Works with Python 3 version of ``MyProxyClient``.
- Testing structure with ``pytest`` has been improved.

0.1.8 (2017-01-03)
------------------

This release includes the following changes:

- The tests have been updated and various fixes made to make them match the up-to-date ESGF Search API.
- Following problems with the search being slow in certain scenarios an extra call to the Search service
  was made optional through the ``SearchContext.search()`` method. If you send the argument and value
  of ``ignore_facet_check=True`` then this hidden call to the service will be avoided. This typically saves
  2 seconds of wait time which can be very important in some iterative search scenarios.
- The ``SearchContext.search()`` method was also extended so that the argument ``batch_size`` could be
  directly sent to it in order to manage how the calls to the API would be separated out into batches. This
  does not affect the final result but may affect the speed of the response. The batch size can also be set
  as a default in the ``pyesgf.search.consts`` module.
- Searches at the file-level now return a ``gridftp_url`` property along with other existing properties such
  as ``download_url``.

0.1.6 (2016-05-16)
------------------

This release includes a fix for Issue #4 to cope with ESGF Search end points
being given with or without a ":port" component in the host address.

0.1.1 (2013-04-15)
------------------

This release will include wget script download support.

.. warning::
   The expected value of the *url* parameter to ``SearchConnection()`` has changed in this release.
   Prior to v0.1.1 the *url* parameter expected the full URL of the
   search endpoint up to the query string.  This has now been changed
   to expect *url* to omit the final endpoint name,
   e.g. ``https://esgf-node.llnl.gov/esg-search/search`` should be changed
   to ``https://esgf-node.llnl.gov/esg-search`` in client code.  The
   current implementation detects the presence of ``/search`` and
   corrects the URL to retain backward compatibility but this feature
   may not remain in future versions.

This release changes the call signature of ``SearchConnection.send_query()`` and
introduces the additional methods ``send_search()`` and ``send_wget()``.
When upgrading code to work with this new API simly:

1. Change the *url* parameter to ``SearchConnection()`` to not include the ``/search`` suffix
2. Change any occurrence of ``send_query()`` to ``send_search()``

0.1b1 (2013-01-19)
------------------

This release marks the start of the 0.1 series which is considered beta-quality.
API changes in this series will be clearly marked in the documentation and backward-compatible
releases will be maintained on pypi.

The 0.1b1 release includes integrated MyProxy logon support in the ``pyesgf.logon`` module.
This release also includes optimisations to the search system to avoid querying multiple shards
when requesting the files from a dataset.
