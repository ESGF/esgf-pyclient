"""
An interface to the `ESGF Search API`_

 :author: Stephen Pascoe

Search parameter categories
---------------------------

We divide the parameters to the ESGF serach API into 4 categories

1. Connection parameters: distrib, shards.  These are best set at the connection level.
2. Search configuration parameters: type, latest, facets, fields, from/to, replica.  These configure the search response and constrain the results in ways not related to the data.
3. Constraint parameters: facet names, query, start/end and lat/lon/bbox/location/radius/polygon.  These are parameters directly related to the data.
4. Hidden parameters: limit, offset.  These are hidden within the client code so the user doesn't need to deal with them.

Specifying Facet constraints
----------------------------

There are 3 ways to specify multiple values to a facet in the API:
 1. Using a query string 'facet=value1&facet=values2'.  This returns the logical OR of applying the constraints
 2. Using a query string 'facet=value1,value2'.  This returns the logical AND of applying the constraints
 3. Within the freetext search keyword "query"

We will leave method 3 completely open to the user and encompass 1&2 into a single constraint data structure as follows:

 facet_constraints = {facet_name: facet_constraint, ...}
 facet_constraint = facet_value | [facet_value, facet_value, ...]
 facet_value = string | (ALL_OF, facet_value, facet_value, facet_value)

A convenience function is supplied for specifying all_of

E.g. you could specify a search accross 2 experiments for datasets containing both variables 'tas' and 'pr':
 search_context.search(experiment=['piControl', 'historical'], variable=all_of('tas', 'pr'))

Examples
--------

>>> conn = SearchConnection('http://pcmdi9.llnl.gov/esg-search')
>>> ctx = conn.new_context(project='cmip5')
>>> ctx.facet_counts
#... List all facets available for project=cmip5
>>> ctx2 = ctx.constrain(experiment='piControl')
>>> ctx2.facet_counts
#... List all facets available for project=cmip5, experiment='piControl'
>>> ctx2.constraints
{'project': 'cmip5', 'experiment': 'piControl', 'model': 'HadGEM2-ES'}

>>> results = ctx2.search(model='HadGEM2-ES', ensemble='r1i1p1')

# Results is a sequence type which caches responses from the server
>>> len(results)
424242
>>> results[:20]
#... automatically asks for the next 10 results

# You can retrieve the original SearchContext used for these results
>>> ctx3 = results.context
>>> ctx3.constraints
{'project': 'cmip5', 'experiment': 'piControl', 'model': 'HadGEM2-ES', 'ensemble': 'r1i1p1'}

# Each result is a dictionary of values and lists of values
>>> results[5]
      {
        'id':'cmip5.output1.CMCC.CMCC-CM.piControl.3hr.atmos.3hr.r1i1p1.v20120330|adm07.cmcc.it',
        'version':'20120330',
        'cf_standard_name':['cloud_area_fraction',
          'surface_upward_latent_heat_flux',
          'surface_upward_sensible_heat_flux',
          'precipitation_flux',
#...
        'description':['CMCC-CM model output prepared for CMIP5 pre-industrial control'],
        'drs_id':['cmip5.output1.CMCC.CMCC-CM.piControl.3hr.atmos.3hr.r1i1p1'],
        'ensemble':['r1i1p1'],
        'experiment':['piControl'],
        'experiment_family':['All',
          'Control'],
        'forcing':['Nat,GHG,SA,TO,Sl'],
        'format':['netCDF, CF-1.4'],
        'index_node':'adm07.cmcc.it',
#...
}


.. _`ESGF Search API`: http://esgf.org/wiki/ESGF_Search_API

"""

from .connection import SearchConnection
from .context import SearchContext
from .constraints import GeospatialConstraint, all_of
from .results import ResultSet
from .consts import TYPE_DATASET, TYPE_FILE


__version__ = '0.0.1'

#!TODO: ResultFormatter class.  process response json to specialise the result json.  Default is None
#!TODO: pipe results to new process.  Command-line interface.
#!TODO: Helper methods for "get opendap" "get download urls"

    
    

    
