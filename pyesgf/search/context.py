
import copy

from .constraints import GeospatialConstraint
from .consts import TYPE_DATASET, TYPE_FILE, QUERY_KEYWORD_TYPES
from .results import ResultSet

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
                 from_timestamp=None, to_timestamp=None,
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
        self.__facet_counts = None
        self.__hit_count = None
        
        #  Constraints
        self.freetext_constraint = None
        self.facet_constraints = {}
        self.temporal_constraint = (None, None)
        self.geosplatial_constraint = None

        self._update_constraints(constraints)

	# Search configuration parameters
        self.timestamp_range = (from_timestamp, to_timestamp)
	self.type = type
	self.latest = latest
	self.facets = facets
        self.fields = fields
        self.replica = replica

    #-------------------------------------------------------------------------
    # Functional search interface
    # These do not change the constraints on self.

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

        self.__update_counts()
        
        return ResultSet(sc)

    def constrain(self, **constraints):
        """
        Return a *new* instance with the additional constraints.
        
        """
        new_sc = copy.copy(self)
        new_sc._update_constraints(constraints)
	return new_sc


    @property
    def facet_counts(self):
        self.__update_counts()
        return self.__facet_counts

    @property
    def hit_count(self):
        self.__update_counts()
        return self.__hit_count

    def __update_counts(self):
        # If hit_count is set the counts are already retrieved
        if self.__hit_count is not None:
            return
        
        self.__facet_counts = {}
        self.__hit_count = None
        query_dict = self._build_query()
        query_dict['facets'] = '*'

        response = self.connection.send_query(query_dict, limit=0)
        for facet, counts in (
                response['facet_counts']['facet_fields'].items()):
            d = self.__facet_counts[facet] = {}
            while counts:
                d[counts.pop()] = counts.pop()

        self.__hit_count = response['response']['numFound']
                
    #-------------------------------------------------------------------------
    # Constraint mutation interface
    # These functions update the instance in-place.
    # Use constrain() and search() to generate new contexts with tighter
    # constraints.

    def _update_constraints(self, constraints):
        """
        Update the constraints in-place by calling _constrain_*() methods.
        
        """
        constraints_split = self._split_constraints(constraints)
        self._constrain_facets(constraints_split['facet'])
        self._constrain_freetext(constraints_split['freetext'].get('query'))

        #!TODO: implement temporal and geospatial constraints
        #self._constrain_temporal()
        #self._constrain_geospatial()

        # reset cached values
        self.__hit_count = None
        self.__facet_counts = None

    def _constrain_facets(self, facet_constraints):
        self.facet_constraints.update(facet_constraints)
    
    def _constrain_freetext(self, query):
        self.freetext_constraint = query

    def _constrain_temporal(self, start, end):
        """
        :param start: a datetime instance specifying the start of the temporal
            constraint.
        :param end: a datetime instance specifying the end of the temporal
            constraint.

        """
        #!TODO: support solr date keywords like "NOW" and "NOW-1DAY"
        #     we will probably need a separate TemporalConstraint object
        self.temporal_constraint = (start, end)

    def _constrain_geospatial(self, lat=None, lon=None, bbox=None, location=None,
                 radius=None, polygon=None):
        self.geospatial_constraint = GeospatialConstraint(lat, lon, bbox, location, radius, polygon)

        raise NotImplementedError
        
    #-------------------------------------------------------------------------

    def _split_constraints(self, constraints):
        """
        Divide a constraint dictionary into 4 types of constraints:
        1. Freetext query
        2. Facet constraints
        3. Temporal constraints
        4. Geospatial constraints

        :return: A dictionary of the 4 types of constraint.
        
        """
        # local import to prevent circular importing
        from .connection import query_keyword_type

        constraints_split = dict((kw, {}) for kw in QUERY_KEYWORD_TYPES)
        for kw, val in constraints.items():
            constraint_type = query_keyword_type(kw)
            constraints_split[constraint_type][kw] = val

        return constraints_split
        
    def _build_query(self):
        """
        Build query string parameters as a dictionary.

        """

        query_dict = {"query": self.freetext_constraint,
                      "type": self.type,
                      "latest": self.latest,
                      "facets": self.facets,
                      "fields": self.fields,
                      "replica": self.replica,
                      }
        query_dict.update(self.facet_constraints)
        
        #!TODO: encode datetime
        #start, end = self.temporal_constraint
        #query_dict.update(start=start, end=end)

        return query_dict
    
        
