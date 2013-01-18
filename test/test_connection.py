"""
Test SearchConnection object

"""

#!TODO: replace calls to the a live search service with a mock.
#!TODO: Test for HTTP proxies

import nose.tools as nt

from pyesgf.search.connection import SearchConnection
import pyesgf.search.exceptions as exc

from .config import TEST_SERVICE

def test_blank_query():
    conn = SearchConnection(TEST_SERVICE)
    json = conn.send_query({})

    assert json.keys() == [u'facet_counts', u'responseHeader', u'response']
    
def test_get_shard_list_fail():
    conn = SearchConnection(TEST_SERVICE, distrib=False)
    nt.assert_raises(exc.EsgfSearchException, conn.get_shard_list)

def test_get_shard_list():
    conn = SearchConnection(TEST_SERVICE, distrib=True)
    shards = conn.get_shard_list()
    #!NOTE: the exact shard list will change depending on the shard replication configuration
    #    on the test server
    assert 'localhost' in shards
    assert 'esgf-index1.ceda.ac.uk' in shards
    
    
