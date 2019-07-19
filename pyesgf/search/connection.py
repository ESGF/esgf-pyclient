"""

Module :mod:`pyesgf.search.connection`
======================================

Defines the class representing connections to the ESGF Search API.  To
perform a search create a :class:`SearchConnection` instance then use
:meth:`new_context()` to create a search context.

.. warning::
   Prior to v0.1.1 the *url* parameter expected the full URL of the
   search endpoint up to the query string.  This has now been changed
   to expect *url* to ommit the final endpoint name,
   e.g. ``https://esgf-node.llnl.gov/esg-search/search`` should be changed
   to ``https://esgf-node.llnl.gov/esg-search`` in client code.  The
   current implementation detects the presence of ``/search`` and
   corrects the URL to retain backward compatibility but this feature
   may not remain in future versions.

"""

import requests
import requests_cache
from sqlite3 import DatabaseError
import datetime
import os

import re
from six.moves.urllib.parse import urlparse

import warnings
import logging

from .context import DatasetSearchContext
from .consts import RESPONSE_FORMAT, SHARD_REXP
from .exceptions import EsgfSearchException
from ..multidict import MultiDict
from ..util import urlencode

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class SearchConnection(object):
    """
    :ivar url: The URL to the Search API service.  This should be the URL
        of the ESGF search service excluding the final endpoint name.
        Usually this is http://<hostname>/esg-search
    :ivar distrib: Boolean stating whether searches through this connection are
        distributed.  I.e. whether the Search service distributes the query to
        other search peers.
    :ivar cache: Path to `sqlite` cache file. Cache expires every hours.
    :ivar timeout: Time (in seconds) before query returns an error.
                   Default: 120s.
    :ivar expire_after: Time delta after cache expires. Default: 1 hour.
    :ivar session: requests.session object. optional.
    :ivar verify: boolean, determines if query should be sent over a verified
                  channel.
    """
    # Default limit for queries.  None means use service default.
    default_limit = None

    def __init__(self, url, distrib=True, cache=None, timeout=120,
                 expire_after=datetime.timedelta(hours=1),
                 session=None, verify=True, context_class=None):
        """
        :param context_class: Override the default SearchContext class.

        """
        self.url = url
        self.distrib = distrib
        self.cache = cache
        self.expire_after = expire_after
        self.timeout = timeout
        self.verify = verify
        self._passed_session = session

        # Check URL for backward compatibility
        self.__check_url()

        # _available_shards stores all available shards once
        # retrieved from the server.
        # A value of None means they haven't been retrieved yet.
        # Once set it is a dictionary {'host': [(port, suffix), ...], ...}
        self._available_shards = None

        if context_class:
            self.__context_class = context_class
        else:
            self.__context_class = DatasetSearchContext

        self._isopen = False

    def open(self):
        if (isinstance(self._passed_session, requests.Session) or isinstance(
                self._passed_session, requests_cache.core.CachedSession)):
            self.session = self._passed_session
        else:
            self.session = create_single_session(
                cache=self.cache,
                expire_after=self.expire_after)
        self._isopen = True
        return

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, type, value, traceback):
        self.close()
        return

    def close(self):
        # Close the session
        if not (isinstance(self._passed_session, requests.Session) or isinstance(
                self._passed_session, requests_cache.core.CachedSession)):
            self.session.close()
        self._isopen = False
        return

    def __check_url(self):
        """
        Previous versions of the API expected the full URL to be given
        to SearchConnection's constructure.  This has been deprecated
        in favour of the URL without the final endpoint name in order
        to support other endpoints such as wget.

        This method tests whether self.url looks like an old-style full url and
        fixes the attribute accordingly, raising a depracation warning.

        """

        mo = re.match(r'(.*?)(/search)?/*$', self.url)
        assert mo

        if mo.group(2):
            warnings.warn('Old-style SearchContext URL specified.  '
                          'In future please specify the URL excluding '
                          'the "/search" endpoint.')

        self.url = mo.group(1)

    def send_search(self, query_dict, limit=None, offset=None, shards=None):
        """
        Send a query to the "search" endpoint.
        See :meth:`send_query()` for details.

        :return: The json document for the search results

        """
        full_query = self._build_query(query_dict, limit, offset, shards)
        if not self._isopen:
            self.open()
        response = self._send_query('search', full_query)
        ret = response.json()
        response.close()
        self.close()

        return ret

    def send_wget(self, query_dict, shards=None):
        """
        Send a query to the "search" endpoint.
        See :meth:`send_query()` for details.

        :return: A string containing the script.

        """
        full_query = self._build_query(query_dict, shards=shards)
        if 'type' in full_query:
            del full_query['type']
        if 'format' in full_query:
            del full_query['format']

        self.open()
        response = self._send_query('wget', full_query)
        script = response.text
        response.close()
        self.close()

        return script

    def _send_query(self, endpoint, full_query):
        """
        Generally not to be called directly by the user but via SearchContext
        instances.

        :param full_query: dictionary of query string parameers to send.
        :return: the requests response object from the query.

        """

        log.debug('Query dict is %s' % full_query)

        query_url = '%s/%s?%s' % (self.url, endpoint, urlencode(full_query))
        log.debug('Query request is %s' % query_url)

        response = self.session.get(query_url, verify=self.verify,
                                    timeout=self.timeout)
        if response.status_code == 400:
            # If error code 400, use urllib to find the errors:
            errors = set(re.findall(r"Invalid HTTP query parameter=(\w+)",
                         response.text))
            content = "; ".join([e for e in list(errors)])
            raise Exception("Invalid query parameter(s): %s" % content)

        # Raise if query was unsucessful:
        response.raise_for_status()
        return response

    def _build_query(self, query_dict, limit=None, offset=None, shards=None):
        if shards is not None:
            if self._available_shards is None:
                self._load_available_shards()

            shard_specs = []
            for shard in shards:
                if shard not in self._available_shards:
                    raise EsgfSearchException('Shard %s is not available' %
                                              shard)
                else:
                    for port, suffix in self._available_shards[shard]:
                        # suffix should be ommited when querying
                        if not port:
                            port_string = ""
                        else:
                            port_string = ":%s" % port

                        shard_specs.append('%s%s/solr' % (shard, port_string))

            shard_str = ','.join(shard_specs)
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
        full_query = MultiDict(item for item in full_query.items()
                               if item[1] is not None)

        return full_query

    def _load_available_shards(self):

        # Shards are not available if distrib=False.  The server won't send
        # back a list of shards
        if not self.distrib:
            raise EsgfSearchException('Shard list not available for '
                                      'non-distributed queries')

        self._available_shards = {}

        response_json = self.send_search({'facets': [], 'fields': []})

        try:
            shards = (response_json['responseHeader']['params']['shards']
                      .split(','))
        except KeyError:
            log.debug('_load_available_shards() fails with this exception')
            log.debug('response_json = %s' % response_json)
            raise EsgfSearchException('Error loading available shards')

        # Extract hostname and port from each shard.
        for shard in shards:
            mo = re.match(SHARD_REXP, shard)
            if not mo:
                raise EsgfSearchException('Shard spec %s not recognised' %
                                          shard)
            shard_parts = mo.groupdict()

            # Fix the host if it refers to the local server
            if shard_parts['host'] in ['localhost', '0.0.0.0', '127.0.0.1']:
                parsed_url = urlparse(self.url)
                shard_parts['host'] = parsed_url.hostname

            (self._available_shards.setdefault(shard_parts['host'], [])
             .append((shard_parts['port'], shard_parts['suffix'])))

    def get_shard_list(self):
        """
        return the list of all available shards.  A subset of the returned list
        can be supplied to 'send_query()' to limit the query to selected
        shards.

        Shards are described by hostname and mapped to SOLr shard descriptions
        internally.

        :return: the list of available shards

        """
        if self._available_shards is None:
            self._load_available_shards()

        return self._available_shards

    def new_context(self, context_class=None,
                    latest=None, facets=None, fields=None,
                    from_timestamp=None, to_timestamp=None,
                    replica=None, shards=None, search_type=None,
                    **constraints):
        """
        Returns a :class:`pyesgf.search.context.SearchContext` class for
        performing faceted searches.

        See :meth:`SearchContext.__init__()` for documentation on the
        arguments.

        """
        if context_class is None:
            context_class = self.__context_class

        return context_class(self, constraints,
                             latest=latest, facets=facets, fields=fields,
                             from_timestamp=from_timestamp,
                             to_timestamp=to_timestamp,
                             replica=replica, shards=shards,
                             search_type=search_type)


def query_keyword_type(keyword):
    """
    Returns the keyword type of a search query keyword.

    Possible values are 'system', 'freetext', 'facet', 'temporal' and
    'geospatial'.  If the keyword is unknown it is assumed to be a
    facet keyword

    """
    # !TODO: support "last update" constraints (to/from)

    if keyword == 'query':
        return 'freetext'
    elif keyword in ['start', 'end', 'from_timestamp', 'to_timestamp']:
        return 'temporal'
    elif keyword in ['lat', 'lon', 'bbox', 'location', 'radius', 'polygon']:
        return 'geospatial'
    elif keyword in ['limit', 'from', 'to', 'fields', 'facets', 'format',
                     'type', 'distrib', 'replica', 'id', 'shards']:
        return 'system'
    else:
        return 'facet'


def create_single_session(cache=None, expire_after=datetime.timedelta(hours=1),
                          **kwargs):
    """
    Simple helper function to start a requests or requests_cache session.

    cache, if specified is a filename to a threadsafe sqlite database
    expire_after specifies how long the cache should be kept
    """
    if cache is not None:
        try:
            session = (requests_cache.core
                       .CachedSession(cache,
                                      expire_after=expire_after))
        except DatabaseError:
            # Corrupted cache:
            try:
                os.remove(cache)
            except Exception:
                pass
            session = (requests_cache.core
                       .CachedSession(cache, expire_after=expire_after))
    else:
        session = requests.Session()
    return session
