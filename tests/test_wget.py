"""
Test downloading wget scripts

"""

from pyesgf.search import SearchConnection
from unittest import TestCase


class TestWget(TestCase):
    def setUp(self):
        self.test_service = 'https://esgf.ceda.ac.uk/esg-search'

    def test_download_script(self):
        conn = SearchConnection(self.test_service, distrib=False)
        ctx = conn.new_context(project='CMIP5', ensemble='r1i1p1',
                               model='IPSL-CM5A-LR', realm='seaIce',
                               experiment='historicalGHG')
        script = ctx.get_download_script()
        print(script)

        assert '# ESG Federation download script' in script
        assert '# Search URL: %s' % self.test_service in script
