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

    """
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
	
        if context_class:
            self.__context_class = context_class
        else:
            self.__context_class = DatasetSearchContext
        
        
    def send_query(self, query_dict, limit=None, offset=None, shards=None):
        """
        Generally not to be called directly by the user but via SearchContext
	instances.
        
        :param query_dict: dictionary of query string parameers to send.
        :param shards: None or a subset of :meth:`get_shard_list`.
        :return: ElementTree instance (TODO: think about this)
        
        """
        
        if shards is not None:
            if self._available_shards is None:
                self._load_available_shards()

            for shard in shards:
                if shard not in self._available_shards:
                    raise EsgfSearchException('Shard %s is not available')

            shard_str = ','.join(shards)
        else:
            shard_str = None


        full_query = MultiDict({
            'format': RESPONSE_FORMAT,
            'limit': limit,
            'distrib': 'true' if self.distrib else 'false',
            'offset': offset,
            'shards': shard_str,
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
        return the list of all available shards.  A subset of the returned list can be
        supplied to 'send_query()' to limit the query to selected shards.

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
