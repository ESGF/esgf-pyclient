"""
Test SearchConnection object

"""

#!TODO: replace calls to the a live search service with a mock.
#!TODO: Test for HTTP proxies

from esgf_search.connection import SearchConnection

from .config import TEST_SERVICE

def test_blank_query():
    conn = SearchConnection(TEST_SERVICE)
    json = conn.send_query({})

    assert json.keys() == [u'facet_counts', u'responseHeader', u'response']
    
def test_get_shard_list():
    conn = SearchConnection(TEST_SERVICE)
    shards = conn.get_shard_list()
    assert 'localhost:8983/solr/datasets' in shards
    assert 'pcmdi11.llnl.gov:8983/solr/datasets' in shards

    
