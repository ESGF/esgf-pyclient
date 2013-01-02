"""

Module :mod:`pyesgf.search.connection`
======================================

Defines the class representing connections to the ESGF Search API.


"""

import urllib2, urllib, urlparse
import json
import re

import logging
log = logging.getLogger(__name__)

from .context import DatasetSearchContext
from .consts import RESPONSE_FORMAT, SHARD_REXP
from .exceptions import EsgfSearchException
from pyesgf.multidict import MultiDict
from pyesgf.util import urlencode

class SearchConnection(object):
    """
    :ivar url: The URL to the Search API service.  Usually <prefix>/esgf-search
    :ivar distrib: Boolean stating whether searches through this connection are
        distributed.  I.e. whether the Search service distributes the query to
        other search peers.
    :property shards: List of shards to send the query to.  An empty list implies
        distrib==False.  None implies the default of all shards.  Shards should
        be specified by hostname rather than the ESGF search API syntax of
        <hostname>:<port>/solr/*

    """
    #TODO: we don't need both distrib and shards.

    # Default limit for queries.  None means use service default.
    default_limit = None

    def __init__(self, url, distrib=True, shards=None, 
                 context_class=None):
	"""
        :param context_class: Override the default SearchContext class.

        """
        self.url = url
        self.distrib = distrib

        # _available_shards stores all available shards once retrieved from the server.
        # A value of None means they haven't been retrieved yet.
        self._available_shards = None
        # __shards holds the list of shard keys that are used for querying.
        # None means use the default shard list (i.e. self._available_shards once they
        # have been retrieved.
        self.__shards = None
        # Delay initialising shards if none are specified
        if shards is not None:
            self.shards = shards
	
        if context_class:
            self.__context_class = context_class
        else:
            self.__context_class = DatasetSearchContext
        
        
    def send_query(self, query_dict, limit=None, offset=None):
        """
        Generally not to be called directly by the user but via SearchContext
	instances.
        
        :param query_dict: dictionary of query string parameers to send.
        :return: ElementTree instance (TODO: think about this)
        
        """
        
        if self.distrib and self.__shards is not None:
            shards = ','.join(self._available_shards)
        else:
            shards = None

        full_query = MultiDict({
            'format': RESPONSE_FORMAT,
            'limit': limit,
            'distrib': 'true' if self.distrib else 'false',
            'offset': offset,
            'shards': shards,
            })
        full_query.extend(query_dict)

        # Remove all None valued items
        full_query = MultiDict(item for item in full_query.items() if item[1] is not None)
        log.debug('Query dict is %s' % full_query)

        query_url = '%s?%s' % (self.url, urlencode(full_query))
        log.debug('Query request is %s' % query_url)

        response = urllib2.urlopen(query_url)
        ret = json.load(response)

        return ret

    @property
    def shards(self):
        return __shards

    @shards.setter
    def shards(self, shards):
        """
        Restrict the available shards.  Setting to None will target all 
        available shards.

        Unless shards=None calling this setter will trigger retrieving
        the list of available shards from the server.

        """

        # If set to None this means the default.  The default shard list
        # is not retrieved from the server unless needed
        if shards is None:
            self.__shards = shards
        else:
            if self._available_shards is None:
                self._load_available_shards()

            self.__shards = []
            for shard in shards:
                if shard in self._available_shards:
                    self.__shards.append(shard)
                else:
                    raise EsgfSearchException('Shard %s is not available')

        #!TODO: what if shards=[].  This is meant to mean distrib=False
        return self.__shards

    def _load_available_shards(self):

        # Shards are not available if distrib=False.  The server won't send
        # back a list of shards
        if not self.distrib:
            raise EsgfSearchException('Shard list not available for '
                                      'non-distributed queries')

        self._available_shards = set()

        response_json = self.send_query({'facets': [], 'fields': []})
        shards = response_json['responseHeader']['params']['shards'].split(',')
        
        # Extract hostname and port from each shard.
        for shard in shards:
            mo = re.match(SHARD_REXP, shard)
            if not mo:
                raise EsgfSearchException('Shard spec %s not recognised' %
                                          shard)
            shard_parts = mo.groupdict()
            general_spec = '%(host)s:%(port)s/solr' % shard_parts

            self._available_shards.add(general_spec)


    def get_shard_list(self):
	"""
        return the list of all available shards.  This is not the same as the list
        of shards that will be used in the query which can be obtained from the 'shards' property.


        :return: the list of available shards

        """
        if self._available_shards is None:
            self._load_available_shards()

        return self._available_shards

    
    def new_context(self, context_class=None, **constraints):
	if context_class is None:
            context_class = self.__context_class

	return context_class(self, constraints)


def query_keyword_type(keyword):
    """
    Returns the keyword type of a search query keyword.

    Possible values are 'system', 'freetext', 'facet', 'temporal' and
    'geospatial'.  If the keyword is unknown it is assumed to be a
    facet keyword

    """
    #!TODO: support "last update" constraints (to/from)

    if keyword == 'query':
        return 'freetext'
    elif keyword in ['start', 'end']:
        return 'temporal'
    elif keyword in ['lat', 'lon', 'bbox', 'location', 'radius', 'polygon']:
        return 'geospatial'
    elif keyword in ['limit', 'from', 'to', 'fields', 'facets', 'format',
                     'type', 'distrib', 'replica', 'id', 'shards']:
        return 'system'
    else:
        return 'facet'
