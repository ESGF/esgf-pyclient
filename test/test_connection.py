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
    json = conn.send_search({})

    assert json.keys() == [u'facet_counts', u'responseHeader', u'response']
    
def test_get_shard_list_fail():
    conn = SearchConnection(TEST_SERVICE, distrib=False)
    nt.assert_raises(exc.EsgfSearchException, conn.get_shard_list)

def test_get_shard_list():
    conn = SearchConnection(TEST_SERVICE, distrib=True)
    shards = conn.get_shard_list()
    #!NOTE: the exact shard list will change depending on the shard replication configuration
    #    on the test server
    assert 'esgf-index2.ceda.ac.uk' in shards
    # IPSL now replicates all non-local shards.  Just check it has a few shards
    assert len(shards['esgf-index2.ceda.ac.uk']) > 3
    
    
def test_url_fixing():
    conn1 = SearchConnection(TEST_SERVICE)
    conn2 = SearchConnection(TEST_SERVICE+'/')
    conn3 = SearchConnection(TEST_SERVICE+'///')
    conn4 = SearchConnection(TEST_SERVICE+'/search')
    conn5 = SearchConnection(TEST_SERVICE+'/search///')

    assert conn1.url == conn2.url == conn3.url == conn4.url == conn5.url
