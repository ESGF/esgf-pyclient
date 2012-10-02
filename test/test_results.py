"""
Test the Results classes

"""

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
    download_url = f1.urls['HTTPServer'][0][0]

    # Assumes dataset is published with DRS path.
    ds_subpath = ds_id.replace('.', '/')
    assert ds_subpath.lower() in download_url.lower()


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
