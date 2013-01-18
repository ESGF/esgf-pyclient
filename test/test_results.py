"""
Test the Results classes

"""

import re
from urlparse import urlparse

from pyesgf.search.connection import SearchConnection

from .config import TEST_SERVICE

def test_result1():
    conn = SearchConnection(TEST_SERVICE, distrib=False)

    ctx = conn.new_context(project='CMIP5')
    results = ctx.search()

    r1 = results[0]
    assert r1.dataset_id == 'cmip5.output1.IPSL.IPSL-CM5A-LR.1pctCO2.3hr.atmos.3hr.r1i1p1.v20110427|vesg.ipsl.fr'
    
def test_file_context():
    conn = SearchConnection(TEST_SERVICE, distrib=False)

    ctx = conn.new_context(project='CMIP5')
    results = ctx.search()

    r1 = results[0]
    f_ctx = r1.file_context()

    assert f_ctx.facet_constraints['dataset_id'] == r1.dataset_id

def test_file_list():
    conn = SearchConnection(TEST_SERVICE, distrib=False)

    ctx = conn.new_context(project='CMIP5')
    results = ctx.search()

    r1 = results[0]
    f_ctx = r1.file_context()

    file_results = f_ctx.search()
    f1 = file_results[0]

    ds_id, shard = r1.dataset_id.split('|')
    download_url = f1.download_url

    # Assumes dataset is published with DRS path.
    ds_subpath = ds_id.replace('.', '/')
    assert ds_subpath.lower() in download_url.lower()

def test_file_list2():
    conn = SearchConnection(TEST_SERVICE, distrib=False)

    ctx = conn.new_context(project='CMIP5')
    results = ctx.search()

    r1 = results[0]
    f_ctx = r1.file_context()

    file_results = f_ctx.search()
    for file_result in file_results:
        print file_result.download_url
        assert re.match(r'http://vesg.ipsl.fr/thredds/.*\.nc', file_result.download_url)

def test_aggregations():
    conn = SearchConnection(TEST_SERVICE, distrib=False)

    ctx = conn.new_context(project='CMIP5')
    results = ctx.search()

    r1 = results[0]
    agg_ctx = r1.aggregation_context()

    agg_results = agg_ctx.search()
    agg1 = agg_results[0]

    ds_id, shard = r1.dataset_id.split('|')
    las_url = agg1.urls['LAS'][0][0]

    #!FIXME: A pretty dumb test for a correct aggregation
    assert '.aggregation' in las_url


def test_index_node():
    conn = SearchConnection(TEST_SERVICE, distrib=False)

    ctx = conn.new_context(project='CMIP5')
    results = ctx.search()

    r1 = results[0]
    service = urlparse(TEST_SERVICE)

    assert r1.index_node == service.hostname


def test_other_index_node():
    conn = SearchConnection(TEST_SERVICE, distrib=True)

    ctx = conn.new_context(project='CMIP5', institute='INM')
    results = ctx.search()

    r1 = results[0]
    service = urlparse(TEST_SERVICE)
    print 'index_node = %s' % r1.index_node
    
    assert r1.index_node is not None
    assert r1.index_node != service.hostname

def test_shards_constrain():
    # Test that a file-context constrains the shard list
    
    conn = SearchConnection(TEST_SERVICE, distrib=True)

    ctx = conn.new_context(project='CMIP5')
    results = ctx.search()

    r1 = results[0]
    f_ctx = r1.file_context()

    #!TODO: white-box test.  Refactor.
    query_dict = f_ctx._build_query()
    full_query = f_ctx.connection._build_query(query_dict, shards=f_ctx.shards)

    #!TODO: Force fail to see whether shards is passed through.
    q_shard = full_query['shards']
    # Check it isn't a ',' separated list
    assert ',' not in q_shard
    q_shard_host = q_shard.split(':')[0]
    assert q_shard_host == r1.json['index_node']

    # Now make the query to make sure it returns data from the right index_node
    f_results = f_ctx.search()
    f_r1 = results[0]
    assert f_r1.json['index_node'] == r1.json['index_node']
