"""
Test SearchConnection object

"""

# !TODO: replace calls to the a live search service with a mock.
# !TODO: Test for HTTP proxies

import nose.tools as nt

from pyesgf.search.connection import SearchConnection
import pyesgf.search.exceptions as exc
from unittest import TestCase
import os
import datetime


class TestConnection(TestCase):
    def setUp(self):
        self.test_service = 'http://esgf-index1.ceda.ac.uk/esg-search'
        self.cache = os.path.join(os.path.dirname(__file__), 'url_cache')

    def test_blank_query(self):
        conn = SearchConnection(self.test_service, cache=self.cache)
        json = conn.send_search({})

        assert sorted(json.keys()) == sorted(['facet_counts',
                                              'responseHeader', 'response'])

    def test_get_shard_list_fail(self):
        conn = SearchConnection(self.test_service, cache=self.cache,
                                distrib=False)
        nt.assert_raises(exc.EsgfSearchException, conn.get_shard_list)

    def test_get_shard_list(self):
        conn = SearchConnection(self.test_service, cache=self.cache,
                                distrib=True)
        shards = conn.get_shard_list()
        # !NOTE: the exact shard list will change depending on the shard
        #        replication configuration
        #        on the test server
        assert 'esgf-index2.ceda.ac.uk' in shards
        # IPSL now replicates all non-local shards.
        # Just check it has a few shards
        assert len(shards['esgf-index2.ceda.ac.uk']) > 3

    def test_url_fixing(self):
        # Switch off warnings for this case because we are testing that issue
        import warnings
        warnings.simplefilter("ignore")
        conn1 = SearchConnection(self.test_service)
        conn2 = SearchConnection(self.test_service+'/')
        conn3 = SearchConnection(self.test_service+'///')
        conn4 = SearchConnection(self.test_service+'/search')
        conn5 = SearchConnection(self.test_service+'/search///')
        warnings.resetwarnings()

        assert conn1.url == conn2.url == conn3.url == conn4.url == conn5.url

    def test_passed_session(self):
        import requests
        session = requests.session()
        conn = SearchConnection(self.test_service, session=session)
        context = conn.new_context(project='cmip5')
        assert context.facet_constraints['project'] == 'cmip5'

    def test_passed_cached_session(self):
        import requests_cache
        td = datetime.timedelta(hours=1)
        session = requests_cache.core.CachedSession(self.cache,
                                                    expire_after=td)
        conn = SearchConnection(self.test_service, session=session)
        context = conn.new_context(project='cmip5')
        assert context.facet_constraints['project'] == 'cmip5'

    def test_connection_instance(self):
        import requests_cache
        td = datetime.timedelta(hours=1)
        session = requests_cache.core.CachedSession(self.cache,
                                                    expire_after=td)
        with SearchConnection(self.test_service, session=session) as conn:
            context = conn.new_context(project='cmip5')
        assert context.facet_constraints['project'] == 'cmip5'
