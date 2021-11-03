"""

Module :mod:`pyesgf.search.context`
===================================

Defines the :class:`SearchContext` class which represents each ESGF search
query.

"""

import os
import sys
import copy

from webob.multidict import MultiDict

from .constraints import GeospatialConstraint
from .consts import (TYPE_DATASET, TYPE_FILE, TYPE_AGGREGATION,
                     QUERY_KEYWORD_TYPES, DEFAULT_BATCH_SIZE)
from .results import ResultSet
from .exceptions import EsgfSearchException


class SearchContext(object):
    """Instances of this class represent the state of a current search.
    It exposes what facets are available to select and the facet counts
    if they are available.

    Subclasses of this class can restrict the search options.  For instance
    FileSearchContext, DatasetSerachContext or CMIP5SearchContext

    SearchContext instances are connected to SearchConnection instances.  You
    normally create SearchContext instances via one of:
    1. Calling SearchConnection.new_context()
    2. Calling SearchContext.constrain()

    :ivar constraints: A dictionary of facet constraints currently in effect.
        ``constraint[facet_name] = [value, value, ...]``

    :ivar facets: A string containing a comma-separated list of facets to be
        returned (for example ``'source_id,ensemble_id'``). If set, this will
        be used to select which facet counts to include, as returned in the
        ``facet_counts`` dictionary.  Defaults to including all available
        facets, but with distributed searches (where the SearchConnection
        instance was created with ``distrib=True``), some results may be
        missing for server-side reasons when requesting all facets, so a
        warning message will be issued. This contains further details.
    :property facet_counts: A dictionary of available hits with each
        facet value for the search as currently constrained.
        This property returns a dictionary of dictionaries where
        ``facet_counts[facet][facet_value] == hit_count``
    :property hit_count: The total number of hits available with current
                         constraints.

    """

    DEFAULT_SEARCH_TYPE = NotImplemented

    def __init__(self, connection, constraints, search_type=None,
                 latest=None, facets=None, fields=None,
                 from_timestamp=None, to_timestamp=None,
                 replica=None, shards=None):
        """

        :param connection: The SearchConnection
        :param constraints: A dictionary of initial constraints
        :param search_type: One of TYPE_* constants defining the document
            type to search for.  Overrides SearchContext.DEFAULT_SEARCH_TYPE
        :param facets: The list of facets for which counts will be retrieved
            and constraints be validated against.  Or None to represent all
            facets.
        :param fields: A list of field names to return in search responses
        :param replica: A boolean defining whether to return master records
            or replicas, or None to return both.
        :param latest: A boolean defining whether to return only latest
            versions or only non-latest versions, or None to return both.
        :param shards: list of shards to restrict searches to.  Should be from
            the list self.connection.get_shard_list()
        :param from_timestamp: Date-time string to specify start of search
            range (e.g. "2000-01-01T00:00:00Z").
        :param to_timestamp: Date-time string to specify end of search range
            (e.g. "2100-12-31T23:59:59Z").

        """

        self.connection = connection
        self.__facet_counts = None
        self.__hit_count = None
        self._did_facets_star_warning = False
        if search_type is None:
            search_type = self.DEFAULT_SEARCH_TYPE

        #  Constraints
        self.freetext_constraint = None
        self.facet_constraints = MultiDict()
        self.temporal_constraint = [from_timestamp, to_timestamp]
        self.geospatial_constraint = None

        self._update_constraints(constraints)

        # Search configuration parameters
        self.timestamp_range = (from_timestamp, to_timestamp)

        search_types = [TYPE_DATASET, TYPE_FILE, TYPE_AGGREGATION]
        if search_type not in search_types:
            raise EsgfSearchException('search_type must be one of %s'
                                      % ','.join(search_types))
        self.search_type = search_type

        self.latest = latest
        self.facets = facets
        self.fields = fields
        self.replica = replica
        self.shards = shards

    # -------------------------------------------------------------------------
    # Functional search interface
    # These do not change the constraints on self.

    def search(self, batch_size=DEFAULT_BATCH_SIZE, ignore_facet_check=False,
               **constraints):
        """
        Perform the search with current constraints returning a set of results.

        :batch_size: The number of results to get per HTTP request.
        :ignore_facet_check: Do not make an extra HTTP request to populate
            :py:attr:`~facet_counts` and :py:attr:`~hit_count`.
        :param constraints: Further constraints for this query.  Equivalent
            to calling ``self.constrain(**constraints).search()``
        :return: A ResultSet for this query

        """
        if constraints:
            sc = self.constrain(**constraints)
        else:
            sc = self

        if not ignore_facet_check:
            sc.__update_counts()

        return ResultSet(sc, batch_size=batch_size)

    def constrain(self, **constraints):
        """
        Return a *new* instance with the additional constraints.

        """
        new_sc = copy.deepcopy(self)
        new_sc._update_constraints(constraints)
        return new_sc

    def get_download_script(self, **constraints):
        """
        Download a script for downloading all files in the set of results.

        :param constraints: Further constraints for this query. Equivalent
            to calling ``self.constrain(**constraints).get_download_script()``
        :return: A string containing the script
        """
        if constraints:
            sc = self.constrain(**constraints)
        else:
            sc = self

        sc.__update_counts()

        query_dict = sc._build_query()

        # !TODO: allow setting limit
        script = sc.connection.send_wget(query_dict,
                                         shards=self.shards)

        return script

    @property
    def facet_counts(self):
        self.__update_counts()
        return self.__facet_counts

    @property
    def hit_count(self):
        self.__update_counts()
        return self.__hit_count

    def get_facet_options(self):
        """
        Return a dictionary of facet counts filtered to remove all
        facets that are completely constrained.  This method is
        similar to the property ``facet_counts`` except facet values
        which are not relevant for further constraining are removed.

        """
        facet_options = {}
        hits = self.hit_count
        for facet, counts in list(self.facet_counts.items()):
            # filter out counts that match total hits
            counts = dict(items for items in list(counts.items())
                          if items[1] < hits)
            if len(counts) > 1:
                facet_options[facet] = counts

        return facet_options

    def __update_counts(self):
        # If hit_count is set the counts are already retrieved
        if self.__hit_count is not None:
            return

        self.__facet_counts = {}
        self.__hit_count = None
        query_dict = self._build_query()

        if self.facets:
            query_dict['facets'] = self.facets
        else:
            query_dict['facets'] = '*'
            if self.connection.distrib:
                self._do_facets_star_warning()

        response = self.connection.send_search(query_dict, limit=0)
        for facet, counts in (list(response['facet_counts']['facet_fields'].items())):
            d = self.__facet_counts[facet] = {}
            while counts:
                d[counts.pop()] = counts.pop()

        self.__hit_count = response['response']['numFound']

    def _do_facets_star_warning(self):
        env_var_name = 'ESGF_PYCLIENT_NO_FACETS_STAR_WARNING'
        if env_var_name in os.environ:
            return
        if not self._did_facets_star_warning:
            sys.stderr.write(f'''
-------------------------------------------------------------------------------
Warning - defaulting to search with facets=*

This behavior is kept for backward-compatibility, but ESGF indexes might not
successfully perform a distributed search when this option is used, so some
results may be missing.  For full results, it is recommended to pass a list of
facets of interest when instantiating a context object.  For example,

      ctx = conn.new_context(facets='project,experiment_id')

Only the facets that you specify will be present in the facets_counts dictionary.

This warning is displayed when a distributed search is performed while using the
facets=* default, a maximum of once per context object.  To suppress this warning,
set the environment variable {env_var_name} to any value
or explicitly use  conn.new_context(facets='*')

-------------------------------------------------------------------------------
''')
            self._did_facets_star_warning = True

    # -------------------------------------------------------------------------
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
        if 'query' in constraints_split['freetext']:
            new_freetext = constraints_split['freetext']['query']
            self._constrain_freetext(new_freetext)

        # !TODO: implement temporal and geospatial constraints
        if 'from_timestamp' in constraints_split['temporal']:
            self.temporal_constraint[0] = (constraints_split['temporal']
                                           ['from_timestamp'])
        if 'to_timestamp' in constraints_split['temporal']:
            self.temporal_constraint[1] = (constraints_split['temporal']
                                           ['to_timestamp'])
        # self._constrain_geospatial()

        # reset cached values
        self.__hit_count = None
        self.__facet_counts = None

    def _constrain_facets(self, facet_constraints):
        for key, values in list(facet_constraints.mixed().items()):
            current_values = self.facet_constraints.getall(key)
            if isinstance(values, list):
                for value in values:
                    if value not in current_values:
                        self.facet_constraints.add(key, value)
            else:
                if values not in current_values:
                    self.facet_constraints.add(key, values)

    def _constrain_freetext(self, query):
        self.freetext_constraint = query

    def _constrain_geospatial(self, lat=None, lon=None, bbox=None,
                              location=None, radius=None, polygon=None):
        self.geospatial_constraint = GeospatialConstraint(
                                            lat, lon, bbox, location,
                                            radius, polygon)

        raise NotImplementedError

    # -------------------------------------------------------------------------

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

        constraints_split = dict((kw, MultiDict()) for kw
                                 in QUERY_KEYWORD_TYPES)

        for kw, val in list(constraints.items()):
            constraint_type = query_keyword_type(kw)
            constraints_split[constraint_type][kw] = val

        return constraints_split

    def _build_query(self):
        """
        Build query string parameters as a dictionary.

        """

        query_dict = MultiDict({"query": self.freetext_constraint,
                                "type": self.search_type,
                                "latest": self.latest,
                                "facets": self.facets,
                                "fields": self.fields,
                                "replica": self.replica})

        query_dict.extend(self.facet_constraints)

        # !TODO: encode datetime
        start, end = self.temporal_constraint
        query_dict.update(start=start, end=end)

        return query_dict


class DatasetSearchContext(SearchContext):
    DEFAULT_SEARCH_TYPE = TYPE_DATASET


class FileSearchContext(SearchContext):
    DEFAULT_SEARCH_TYPE = TYPE_FILE


class AggregationSearchContext(SearchContext):
    DEFAULT_SEARCH_TYPE = TYPE_AGGREGATION
