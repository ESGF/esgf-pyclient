"""
Test SearchConnection object

"""

# !TODO: replace calls to the a live search service with a mock.
# !TODO: Test for HTTP proxies

import nose.tools as nt

from pyesgf.search.connection import SearchConnection
import pyesgf.search.exceptions as exc
from unittest import TestCase


class TestConnection(TestCase):
    def setUp(self):
        self.test_service = 'http://esgf-index1.ceda.ac.uk/esg-search'

    def test_blank_query(self):
        conn = SearchConnection(self.test_service)
        json = conn.send_search({})

        assert json.keys() == [u'facet_counts', u'responseHeader', u'response']

    def test_get_shard_list_fail(self):
        conn = SearchConnection(self.test_service, distrib=False)
        nt.assert_raises(exc.EsgfSearchException, conn.get_shard_list)

    def test_get_shard_list(self):
        conn = SearchConnection(self.test_service, distrib=True)
        shards = conn.get_shard_list()
        # !NOTE: the exact shard list will change depending on the shard
        #        replication configuration
        #        on the test server
        assert 'esgf-index2.ceda.ac.uk' in shards
        # IPSL now replicates all non-local shards.
        # Just check it has a few shards
        assert len(shards['esgf-index2.ceda.ac.uk']) > 3

    def test_url_fixing(self):
        conn1 = SearchConnection(self.test_service)
        conn2 = SearchConnection(self.test_service+'/')
        conn3 = SearchConnection(self.test_service+'///')
        conn4 = SearchConnection(self.test_service+'/search')
        conn5 = SearchConnection(self.test_service+'/search///')

        assert conn1.url == conn2.url == conn3.url == conn4.url == conn5.url
