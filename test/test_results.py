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
    f_ctx = r1.files_context()

    assert f_ctx.facet_constraints['dataset_id'] == r1.dataset_id
    
