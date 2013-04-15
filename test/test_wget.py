"""
Test downloading wget scripts

"""

from pyesgf.search import SearchConnection, not_equals

from .config import TEST_SERVICE

def test_download_script():
    conn = SearchConnection(TEST_SERVICE, distrib=False)
    ctx = conn.new_context(project='CMIP5', ensemble='r1i1p1', model='IPSL-CM5A-LR', realm='seaIce',
                           experiment='historicalGHG')
    script = ctx.get_download_script()

    assert '# ESG Federation download script' in script
    assert '# Search URL: %s' % TEST_SERVICE in script
