"""
Defines the class representing connections to the ESGF Search API.

:author: Stephen Pascoe

"""

import urllib2, urllib, urlparse
import json

import logging
log = logging.getLogger(__name__)

from .context import SearchContext

RESPONSE_FORMAT='application/solr+json'

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

    # Default limit for queries.  None means use service default.
    default_limit = None

    def __init__(self, url, distrib=True, shards=None, 
                 context_class=None):
	"""
        :param context_class: Override the default SearchContext class.

        """
        self.url = url
        self.distrib = distrib
        self.shards = shards
	
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
        
        full_query = {
            'format': RESPONSE_FORMAT,
            }
        full_query.update(query_dict)
        if limit is not None:
            full_query['limit'] = limit
        if distrib is not None:
            full_query['distrib'] = distrib
        if shards is not None:
            full_query['shards'] = ','.join(shards)

        query_url = '%s?%s' % (self.url, urllib.urlencode(full_query))
        log.debug('Query request is %s' % query_url)

        response = urllib2.urlopen(query_url)
        ret = json.load(response)

        return ret
    

    def get_shard_list(self):
	"""
        :return: the list of available shards

        """
        response = self.send_query({'facets': [], 'fields': []})
        shards = response['responseHeader']['params']['shards'].split(',')
        
        return shards
    
    def new_context(self, **constraints):
	#!MAYBE: context_class=None, 
	return self.__context_class(self, constraints)
