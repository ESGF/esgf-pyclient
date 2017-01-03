

Search Concepts
===============

The :mod:`pyesgf.search` interface to ESGF search reflects the typical workflow of a user navigating through the sets of facets categorising available data.  


Keyword classification
----------------------

The keyword arguments described in the `ESGF Search API`_ have a wide veriety of roles within the search workflow.  To reflect this :mod:`pyesgf.search` classifies these keywords into system, spatiotemporal and facet keywords.  Responsibility for these keywords are distributes across several classes.


System keywords
'''''''''''''''

===========  ================  =================================================================================================== 
API keyword  class             Notes
===========  ================  =================================================================================================== 
limit        SearchConnection  Set in :meth:`SearchConnection:send_query` method or transparently through :class:`SearchContext`
offset       SearchConnection  Set in :meth:`SearchConnection:send_query` method or transparently through :class:`SearchContext`
shards       SearchConnection  Set in constructor
distrib      SearchConnection  Set in constructor
latest       SearchContext     Set in constructor
facets       SearchContext     Set in constructor
fields       SearchContext     Set in constructor
replica      SearchContext     Set in constructor
type         SearchContext     Create contexts with the right type using :meth:`ResultSet.file_context`, etc.
from         SearchContext     Set in constructor. Use "from_timestamp" in the context API.
to           SearchContext     Set in constructor. Use "to_timestamp" in the context API.
fields       n/a               Managed internally
format       n/a               Managed internally
id           n/a               Managed internally
===========  ================  =================================================================================================== 

Temporal keywords
'''''''''''''''''

Temporal keywords are supported for Dataset search. The terms "from_timestamp" and "to_timestamp" should be used with values following the format "YYYY-MM-DDThh:mm:ssZ".

Spatial keywords
''''''''''''''''

Spatial keywords are not yet supported by :mod:`pyesgf.search` however the API does have placeholders for these keywords anticipating future implementation:

Facet keywords
''''''''''''''

All other keywords are considered to be search facets.  The keyword "query" is dealt with specially as a freetext facet.


Main Classes
------------

SearchConnection
''''''''''''''''

:class:`SearchConnection` instances represent a connection to an ESGF Search web service.  This stores the service URL and also service-level parameters like distrib and shards.

SearchContext
'''''''''''''

:class:`SearchContext` represents the constraints on a given search.  This includes the type of records you are searching for (File or Dataset), the list of possible facets with or without facet counts (depending on how the instance is created), currently selected facets/search-terms.  Instances can return the number of hits and facet-counts associated with the current search.

SearchContext objects can be created in several ways:

 1. From a SearchConnection object using the method :meth:`SearchConnection.new_context`
 2. By further constraining an existing FacetContext object.  E.g. new_context = context.constrain(institute='IPSL').
 3. From a Result object using one of it's *foo_context()* methods to create a context for searching for results related to the Result.
 4. Future development may implement project-specific factory.  E.g. CMIP5FacetContext().


ResultSet
'''''''''

:class:`ResultSet` instances are returned by the  :meth:`SearchContext.search` method and represent the results from a query.  They supports transparent paging of results with a client-side cache.  

Result
''''''

:class:`Result` instances represent the result record in the SOLr response.  They are subclassed to represent records of different types: :class:`FileResult` and :class:`DatasetResult`.  Results have various properties exposing information about the objects they represent.  e.g. dataset_id, checksum, filename, size, etc.

.. _`ESGF Search API`: https://github.com/ESGF/esgf.github.io/wiki/ESGF_Search_REST_API
