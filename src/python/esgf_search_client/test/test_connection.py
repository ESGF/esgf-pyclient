"""
Test SearchConnection object

"""

#!TODO: replace calls to the a live search service with a mock.
#!TODO: Test for HTTP proxies

from esgf_search.connection import SearchConnection

TEST_SERVICE='http://esgf-node.ipsl.fr/esg-search'

def test_first_connect():
    conn = SearchConnection(TEST_SERVICE)
    shards = conn.get_shard_list()
    assert 'localhost:8983/solr/datasets' in shards
    assert 'pcmdi9.llnl.gov:8983/solr/datasets' in shards

    
