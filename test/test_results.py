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
    assert re.match(r'cmip5\.output1\.MOHC\..+\|esgf-data2.ceda.ac.uk', r1.dataset_id)
    
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
        assert re.search(r'ds/.*\.nc', file_result.download_url)

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


def test_shards_constrain2():
    # Regression test for issue #8 reported by ian.edmond@metoffice.gov.uk
    conn = SearchConnection('http://pcmdi9.llnl.gov/esg-search',distrib=True)

    ctx = conn.new_context(experiment='piControl', time_frequency='day', variable='pr', ensemble='r1i1p1')
    ctx = ctx.constrain(query='cmip5.output1.BCC.bcc-csm1-1-m.piControl.day.atmos.day.r1i1p1')
    s = ctx.search()

    ds = s[0]

    publicationDataset, server = ds.dataset_id.split('|')
    print publicationDataset, server, ds.json['replica']
    
    searchContext = ds.file_context()
    searchContext=searchContext.constrain(variable='pr')
    for j in searchContext.search():
        print j.download_url, j.checksum, j.checksum_type, j.size

def test_shards_constrain3():
    # Regression test for issue #8 reported by ian.edmond@metoffice.gov.uk
    conn = SearchConnection('http://pcmdi9.llnl.gov/esg-search',distrib=True)

    ctx = conn.new_context(query='cmip5.output1.CMCC.CMCC-CESM.historical.mon.atmos.Amon.r1i1p1.v20130416')
    s = ctx.search()

    ds = s[0]

    publicationDataset, server = ds.dataset_id.split('|')
    print publicationDataset, server, ds.json['replica']
    
    searchContext = ds.file_context()
    searchContext=searchContext.constrain(variable='pr')
    for j in searchContext.search():
        print j.download_url, j.checksum, j.checksum_type, j.size


def test_shards_constrain4():
    # Regression test for issue #8 reported by ian.edmond@metoffice.gov.uk
    conn = SearchConnection('http://pcmdi9.llnl.gov/esg-search',distrib=True)

    ctx = conn.new_context(query='cmip5.output1.BCC.bcc-csm1-1-m.historical.mon.atmos.Amon.r1i1p1.v20120709')
    s = ctx.search()

    ds = s[0]

    publicationDataset, server = ds.dataset_id.split('|')
    print publicationDataset, server, ds.json['replica']
    
    searchContext = ds.file_context()
    searchContext=searchContext.constrain(variable='tas')
    for j in searchContext.search():
        print j.download_url, j.checksum, j.checksum_type, j.size
