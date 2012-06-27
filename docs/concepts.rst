

Main Classes
------------

SearchConnection
''''''''''''''''

A connection to an ESGF Search web service.  This stores the service URL and also service-level parameters like distrib and shards.

SearchContext
'''''''''''''

This represents the constraints on a given search.  This includes the type of records you are searching for (File or Dataset), the list of possible facets with or without facet counts (depending on how the instance is created), currently selected facets/search-terms.

FacetContext objects can be created in several ways:

 1. From a project-specific factory.  E.g. CMIP5FacetContext() could create an instance with the CMIP5 facets pre-configured
 2. By querying a SearchConnection for all available facets for a given record type.
 3. By further constraining an existing FacetContext object.  E.g. fc.constrain(institute='IPSL') --> new_fc.  This would call the SearchConnection to get facet counts of the new constrained FacetContext.

ResultSet
'''''''''

This is the set of results from a query.  It should support paging with a client-side cache.  I.e. an initial query will, by default, return 10 results.  The ResultSet should know how many results are available in total and retrieve further pages on demand.

Result
''''''

This represents the result record in the SOLr response.  It could be a lightweight wrapper around dict.

