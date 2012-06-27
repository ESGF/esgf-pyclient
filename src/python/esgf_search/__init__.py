"""
An interface to the `ESGF Search API`_

 :author: Stephen Pascoe

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
#!TODO: logical AND/OR difference on whether keyword is repeated or coma separated
#!TODO: goespatial/temporal
#!TODO: ResultFormatter class.  process response json to specialise the result json.  Default is None
#!TODO: pipe results to new process.  Command-line interface.
#!TODO: Helper methods for "get opendap" "get download urls"


TYPE_DATASET = 'Dataset'
TYPE_FILE = 'File'

class GeospatialConstraint(object):
    """
    Class to encapsulate all geospatial constraints in the ESGF Search API
    """

    def __init__(self, lat=None, lon=None, bbox=None, location=None,
                 radius=None, polygon=None):
        self.lat, self.lon = lat, lon
        self.bbox = bbox
        self.location = location
        self.radius, self.polygon = radius, polygon


class SearchConnection(object):
    """
    :ivar url: The URL to the Search API service.  Usually <prefix>/esgf-search
    :ivar distrib: Boolean stating whether searches through this connection are
        distributed.  I.e. whether the Search service distributes the query to
        other search peers.
    :ivar shards: List of shards to send the query to.  An empty list implies
        distrib==False.  None implies the default of all shards.
        
    """
    #TODO: we don't need both distrib and shards.

    def __init__(self, url, distrib=True, shards=None, limit=None, 
                 context_class=None):
	"""
        :param context_class: Override the default SearchContext class.

        """
        self.url = url
        self.distrib = distrib
        self.shards = shards
	self.limit = limit
	
        if context_class:
            self.__context_class = context_class
        else:
            self.__context_class = SearchContext
        
        #!TODO: set_shards(). shards should probably be a property.
        
    def send_query(self, query_dict, limit=None, distrib=None, shards=None):
        """
        Generally not to be called directly by the user but via SearchContext
	instances.
        
        :param query_dict: dictionary of query string parameers to send.
        :return: ElementTree instance (TODO: think about this)
        
        """
        raise NotImplementedError

    def get_shard_list(self):
	"""
        :return: the list of available shards

        """
        raise NotImplementedError
    
    def new_context(self, **constraints):
	#!MAYBE: context_class=None, 
	return self.__context_class(self, constraints)


class SearchContext(object):
    """
    Instances of this class represent the state of a current search.
    It exposes what facets are available to select and the facet counts
    if they are available.
    
    Subclasses of this class can restrict the search options.  For instance
    FileSearchContext, DatasetSerachContext or CMIP5SearchContext
    
    SearchContext instances are connected to SearchConnection instances.  You
    normally create SearchContext instances via one of:
    1. Calling SearchConnection.new_context()
    2. Calling SearchContext.constrain()
    
    :ivar constraints: A dictionary of facet constraints currently in effect.
        constraint[facet_name] = [value, value, ...]
        
    """

    def __init__(self, connection, constraints, type=TYPE_DATASET,
		 latest=None, facets=None, fields=None,
		 replica=None):
        """
        :param connection: The SearchConnection
        :param constraints: A dictionary of initial constraints
	:param type: One of TYPE_* constants defining the document type to
	    search for
	:param facets: The list of facets for which counts will be retrieved
	    and constraints be validated against.  Or None to represent all
	    facets.
	:param fields: A list of field names to return in search responses
	:param replica: A boolean defining whether to return master records
	    or replicas, or None to return both.
	:param latest: A boolean defining whether to return only latest verisons
	    or only non-latest versions, or None to return both.

        """
	self.connection = connection
        self.constraints = {}
        self.__update_constraints(constraints)
	
	self.type = type
	self.latest = latest
	self.facets = facets

        # Non facet constraints
        self.from_timestamp, self.to_timestamp = None, None
        self.start, self.end = None, None
        self.query = None
        self.geosplatial_constraint = None

    def search(self, **constraints):
        """
        :param constraints: Further constraints for this query.  Equivilent
            to calling self.constrain(**constraints).search()
        :return: A ResultSet for this query

        """
        if constraints:
            sc = self.constrain(**constraints)
        else:
            sc = self
            
        raise NotImplementedError

    def constrain(self, **constraints):
        new_sc = self.__class__(self.connection, self.constraints)
        new_sc.constrain(**constraints)
	return new_sc
    
    def constrain_timestamp(self, from_timestamp, to_timestamp):
        """
        :param from: a datetime instance specifying the earliest timestamp for
            records returned
        :param to: a datetime instance specifying the latest timestamp for
            records returned
        """
        self.from_timestamp = from_timestamp
        self.to_timestamp = to_timestamp

    def constrain_freetext(self, query):
        self.query = query

    def constrain_temporal(self, start, end):
        """
        :param start: a datetime instance specifying the start of the temporal
            constraint.
        :param end: a datetime instance specifying the end of the temporal
            constraint.

        """
        self.start = start
        self.end = end

    def constrain_geospatial(self, lat=None, lon=None, bbox=None, location=None,
                 radius=None, polygon=None):
        self.geospatial_constraint = GeospatialConstraint(lat, lon, bbox, location, radius, polygon)
        
    @property
    def facet_counts(self):
        raise NotImplementedError

    def __update_constraints(self, constraints):
        raise NotImplementedError

    
class ResultSet(list):
    #!TODO: maybe encapsulate list rather than inherit
    """
    :ivar header:
    :ivar context:

    """

    
