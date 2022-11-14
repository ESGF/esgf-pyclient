"""
Test the Results classes

"""

import re
from urllib.parse import urlparse

import pytest
from unittest import TestCase
from pyesgf.search.connection import SearchConnection


class TestResults(TestCase):

    _test_facets = 'project,model,index_node,data_node'

    def setUp(self):
        self.test_service = 'http://esgf.ceda.ac.uk/esg-search'
        self.test_service_pcmdi = 'https://esgf-node.llnl.gov/esg-search'

    def test_result1(self):
        conn = SearchConnection(self.test_service, distrib=False)

        ctx = conn.new_context(project='CMIP5')
        results = ctx.search()

        r1 = results[0]
        assert re.match(r'cmip5\.output1\..+\|esgf-data1.ceda.ac.uk',
                        r1.dataset_id)

    def test_result1_ignore_facet_check(self):
        conn = SearchConnection(self.test_service, distrib=False)

        ctx = conn.new_context(project='CMIP5')
        results = ctx.search(ignore_facet_check=True)

        r1 = results[0]
        assert re.match(r'cmip5\.output1\..+\|esgf-data1.ceda.ac.uk',
                        r1.dataset_id)

    def test_file_context(self):
        conn = SearchConnection(self.test_service, distrib=False)

        ctx = conn.new_context(project='CMIP5')
        results = ctx.search()

        r1 = results[0]
        f_ctx = r1.file_context()

        assert f_ctx.facet_constraints['dataset_id'] == r1.dataset_id

    @pytest.mark.slow
    def test_file_list(self):
        conn = SearchConnection(self.test_service, distrib=False)

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

    @pytest.mark.slow
    def test_file_list2(self):
        conn = SearchConnection(self.test_service, distrib=False)

        ctx = conn.new_context(project='CMIP5')
        results = ctx.search()

        r1 = results[0]
        f_ctx = r1.file_context()

        file_results = f_ctx.search()
        for file_result in file_results:
            assert re.search(r'ds/.*\.nc', file_result.download_url)

    @pytest.mark.slow
    def test_gridftp_url_in_file_result(self):
        conn = SearchConnection(self.test_service, distrib=False)

        ctx = conn.new_context(project='CMIP5')
        results = ctx.search()

        r1 = results[0]
        f_ctx = r1.file_context()

        file_results = f_ctx.search()
        for file_result in file_results:
            gridftp_url = file_result.gridftp_url
            assert gridftp_url.split(":")[0] == "gsiftp"
            assert file_result.gridftp_url.endswith(".nc")

    @pytest.mark.slow
    def test_globus_url_in_file_result(self):
        conn = SearchConnection(self.test_service, distrib=False)

        ctx = conn.new_context(project='CMIP5')
        results = ctx.search()

        r1 = results[0]
        f_ctx = r1.file_context()

        file_results = f_ctx.search()
        for file_result in file_results:
            globus_url = file_result.globus_url
            assert globus_url.split(":")[0] == "globus"
            assert file_result.globus_url.endswith(".nc")

    @pytest.mark.slow
    def test_aggregations(self):
        conn = SearchConnection(self.test_service, distrib=False)

        ctx = conn.new_context(project='CMIP5')
        results = ctx.search()

        r1 = results[0]
        agg_ctx = r1.aggregation_context()

        agg_results = agg_ctx.search()
        agg1 = agg_results[0]

        ds_id, shard = r1.dataset_id.split('|')
        las_url = agg1.urls['LAS'][0][0]

        # !FIXME: A pretty dumb test for a correct aggregation
        assert '.aggregation' in las_url

    def test_index_node(self):
        conn = SearchConnection(self.test_service, distrib=False)

        ctx = conn.new_context(project='CMIP5')
        results = ctx.search()

        r1 = results[0]
        service = urlparse(self.test_service)

        assert r1.index_node == service.hostname

    @pytest.mark.slow
    @pytest.mark.xfail(reason='This test fails sometimes ... works locally.')
    def test_other_index_node(self):
        conn = SearchConnection(self.test_service, distrib=True)

        ctx = conn.new_context(project='CMIP5', institute='IPSL')
        results = ctx.search()

        r1 = results[0]
        service = urlparse(self.test_service)
        print(('index_node = %s' % r1.index_node))

        assert r1.index_node is not None
        assert r1.index_node != service.hostname

    @pytest.mark.skip(reason='This test does not work - to be removed?')
    def test_shards_constrain(self):
        # Test that a file-context constrains the shard list
        conn = SearchConnection(self.test_service, distrib=True)

        ctx = conn.new_context(project='CMIP5')
        results = ctx.search()

        r1 = results[0]
        f_ctx = r1.file_context()

        # !TODO: white-box test.  Refactor.
        query_dict = f_ctx._build_query()
        full_query = f_ctx.connection._build_query(query_dict,
                                                   shards=f_ctx.shards)

        # !TODO: Force fail to see whether shards is passed through.
        # NOTE: 'shards' is NOT even a key in this dictionary. Needs rewrite!!!
        q_shard = full_query['shards']
        # Check it isn't a ',' separated list
        assert ',' not in q_shard
        q_shard_host = q_shard.split(':')[0]
        assert q_shard_host == r1.json['index_node']

        # Now make the query to make sure it returns data from
        # the right index_node
        f_results = f_ctx.search()
        f_r1 = f_results[0]
        assert f_r1.json['index_node'] == r1.json['index_node']

    @pytest.mark.slow
    def test_shards_constrain2(self):
        # Regression test for issue #8 reported by ian.edmond@metoffice.gov.uk
        conn = SearchConnection(self.test_service_pcmdi, distrib=True)

        ctx = conn.new_context(experiment='piControl', time_frequency='day',
                               variable='pr', ensemble='r1i1p1')
        ctx = ctx.constrain(query=('cmip5.output1.BCC.bcc-csm1-1-m.piControl.'
                                   'day.atmos.day.r1i1p1'))
        s = ctx.search()

        ds = s[0]

        publicationDataset, server = ds.dataset_id.split('|')
        print((publicationDataset, server, ds.json['replica']))

        searchContext = ds.file_context()
        searchContext = searchContext.constrain(variable='pr')
        for j in searchContext.search():
            print((j.download_url, j.checksum, j.checksum_type, j.size))

    @pytest.mark.slow
    def test_shards_constrain3(self):
        # Regression test for issue #8 reported by ian.edmond@metoffice.gov.uk
        conn = SearchConnection(self.test_service_pcmdi, distrib=True)

        ctx = conn.new_context(query=('cmip5.output1.CMCC.CMCC-CESM.'
                                      'historical.mon.atmos.Amon.r1i1p1.'
                                      'v20130416'))
        s = ctx.search()

        ds = s[0]

        publicationDataset, server = ds.dataset_id.split('|')
        print((publicationDataset, server, ds.json['replica']))

        searchContext = ds.file_context()
        searchContext = searchContext.constrain(variable='pr')
        for j in searchContext.search():
            print((j.download_url, j.checksum, j.checksum_type, j.size))

    @pytest.mark.slow
    def test_shards_constrain4(self):
        # Regression test for issue #8 reported by ian.edmond@metoffice.gov.uk
        conn = SearchConnection(self.test_service_pcmdi, distrib=True)

        ctx = conn.new_context(query=('id:cmip5.output1.BCC.bcc-csm1-1-m.'
                                      'historical.mon.atmos.Amon.r1i1p1.'
                                      'v20120709*'))
        s = ctx.search()

        ds = s[0]

        publicationDataset, server = ds.dataset_id.split('|')
        print((publicationDataset, server, ds.json['replica']))

        searchContext = ds.file_context()
        searchContext = searchContext.constrain(variable='tas')
        for j in searchContext.search():
            print((j.download_url, j.checksum, j.checksum_type, j.size))

    def _test_batch_size_has_no_impact_on_results(self, facets=None):

        # should work in principle with distrib=True, but use distrib=False
        # because sometimes returned results misses results from some other indexes
        # and we don't want this to cause a failure

        conn = SearchConnection(self.test_service, distrib=False)

        constraints = {
            'mip_era': 'CMIP6',
            'institution_id': 'CCCma',
            'experiment_id': 'pdSST-pdSIC',
            'table_id': 'Amon',
            'variable_id': 'ua',
            'facets': facets}
        ctx = conn.new_context(**constraints)

        results = ctx.search(batch_size=50)
        ids_batch_size_50 = sorted(results, key=lambda x: x.dataset_id)

        ctx = conn.new_context(**constraints)
        results = ctx.search(batch_size=100)
        ids_batch_size_100 = sorted(results, key=lambda x: x.dataset_id)

        assert len(ids_batch_size_50) == len(ids_batch_size_100)

    @pytest.mark.slow
    def test_batch_size_has_no_impact_on_results_with_few_facets(self):
        self._test_batch_size_has_no_impact_on_results(
            facets=self._test_facets)
