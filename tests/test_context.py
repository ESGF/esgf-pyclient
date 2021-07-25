"""
Test the SearchContext class

"""

import pytest

from pyesgf.search import SearchConnection, not_equals
from unittest import TestCase
import os


class TestContext(TestCase):

    _test_few_facets = 'project,model,index_node,data_node'

    def setUp(self):
        self.test_service = 'http://esgf-data.dkrz.de/esg-search'
        self.cache = os.path.join(os.path.dirname(__file__), 'url_cache')

    def test_context_freetext(self):
        conn = SearchConnection(self.test_service, cache=self.cache)
        context = conn.new_context(query="temperature")

        self.assertTrue(context.freetext_constraint == "temperature")

    def test_context_facets2(self):
        conn = SearchConnection(self.test_service, cache=self.cache)
        context = conn.new_context(project='CMIP5')

        context2 = context.constrain(model="IPSL-CM5A-LR")
        self.assertTrue(context2.facet_constraints['project'] == 'CMIP5')
        self.assertTrue(context2.facet_constraints['model'] == 'IPSL-CM5A-LR')

    def test_context_facets_multivalue(self):
        conn = SearchConnection(self.test_service, cache=self.cache)
        context = conn.new_context(project='CMIP5')

        context2 = context.constrain(model=['IPSL-CM5A-LR', 'IPSL-CM5A-MR'])
        self.assertTrue(context2.hit_count > 0)

        self.assertTrue(context2.facet_constraints['project'] == 'CMIP5')
        self.assertTrue(sorted(context2.facet_constraints.getall('model')) == ['IPSL-CM5A-LR', 'IPSL-CM5A-MR'])

    def test_context_facet_multivalue2(self):
        conn = SearchConnection(self.test_service, cache=self.cache)
        context = conn.new_context(project='CMIP5', model='IPSL-CM5A-MR')
        self.assertTrue(
            context.facet_constraints.getall('model') == ['IPSL-CM5A-MR'])

        context2 = context.constrain(model=['IPSL-CM5A-MR', 'IPSL-CM5A-LR'])
        self.assertTrue(sorted(context2.facet_constraints.getall('model')) == ['IPSL-CM5A-LR', 'IPSL-CM5A-MR'])

    def test_context_facet_multivalue3(self):
        conn = SearchConnection(self.test_service, cache=self.cache)
        ctx = conn.new_context(project='CMIP5', query='humidity',
                               experiment='rcp45')
        hits1 = ctx.hit_count
        self.assertTrue(hits1 > 0)
        ctx2 = conn.new_context(project='CMIP5', query='humidity',
                                experiment=['rcp45', 'rcp85'])
        hits2 = ctx2.hit_count

        self.assertTrue(hits2 > hits1)

    def test_context_facet_options(self):
        conn = SearchConnection(self.test_service, cache=self.cache)
        context = conn.new_context(project='CMIP5', model='IPSL-CM5A-LR',
                                   ensemble='r1i1p1', experiment='rcp60',
                                   realm='seaIce')

        expected = sorted(['access', 'index_node', 'data_node', 'format',
                           'cf_standard_name', 'variable_long_name',
                           'cmor_table', 'time_frequency', 'variable'])
        self.assertTrue(sorted(context.get_facet_options().keys()) == expected)

    def test_context_facets3(self):
        conn = SearchConnection(self.test_service, cache=self.cache)

        context = conn.new_context(project='CMIP5')
        context2 = context.constrain(model="IPSL-CM5A-LR")

        results = context2.search()
        result = results[0]

        self.assertTrue(result.json['project'] == ['CMIP5'])
        self.assertTrue(result.json['model'] == ['IPSL-CM5A-LR'])

    def test_facet_count(self):
        conn = SearchConnection(self.test_service, cache=self.cache)

        context = conn.new_context(project='CMIP5')
        context2 = context.constrain(model="IPSL-CM5A-LR")

        counts = context2.facet_counts
        self.assertTrue(list(counts['model'].keys()) == ['IPSL-CM5A-LR'])
        self.assertTrue(list(counts['project'].keys()) == ['CMIP5'])

    
    def _test_distrib(self, constraints=None, test_service=None,
                      cache=None):
        if constraints == None:
            constraints={}
        if test_service == None:
            test_service = self.test_service
        
        conn1 = SearchConnection(test_service, distrib=False, cache=cache)
        context1 = conn1.new_context(**constraints)
        count1 = context1.hit_count

        conn2 = SearchConnection(test_service, distrib=True, cache=cache)
        context2 = conn2.new_context(**constraints)
        count2 = context2.hit_count

        assert count1 < count2


    _distrib_constraints_few_facets = {'project': 'CMIP5',
                                       'facets': _test_few_facets}
    _distrib_constraints_all_facets = {'project': 'CMIP5',
                                       'facets': '*'}

    def test_distrib_with_few_facets(self):
        self._test_distrib(constraints=self._distrib_constraints_few_facets)

    @pytest.mark.slow
    @pytest.mark.xfail
    # Expected failure: with facets=* the distrib=true appears to be 
    # ignored.  This is observed both on the CEDA and also DKRZ index nodes 
    # (the only nodes investigated).
    def test_distrib_with_all_facets(self):
        self._test_distrib(constraints=self._distrib_constraints_all_facets)

    # @pytest.mark.skip(reason="cache fails on python 3.7")
    def test_distrib_with_cache_with_few_facets(self):
        self._test_distrib(constraints=self._distrib_constraints_few_facets,
                           cache=self.cache)

    # @pytest.mark.skip(reason="cache fails on python 3.7")
    @pytest.mark.xfail
    # Expected failure: see test_distrib_all_facets above
    def test_distrib_with_cache_with_all_facets(self):
        self._test_distrib(constraints=self._distrib_constraints_all_facets,
                           cache=self.cache)


    def test_constrain(self):
        conn = SearchConnection(self.test_service, cache=self.cache)

        context = conn.new_context(project='CMIP5')
        count1 = context.hit_count
        context = context.constrain(model="IPSL-CM5A-LR")
        count2 = context.hit_count

        self.assertTrue(count1 > count2)

    def test_constrain_freetext(self):
        conn = SearchConnection(self.test_service, cache=self.cache)

        context = conn.new_context(project='CMIP5', query='humidity')
        self.assertTrue(context.freetext_constraint == 'humidity')

        context = context.constrain(experiment='historical')
        self.assertTrue(context.freetext_constraint == 'humidity')

    def test_constrain_regression1(self):
        conn = SearchConnection(self.test_service, cache=self.cache)

        context = conn.new_context(project='CMIP5', model='IPSL-CM5A-LR')
        self.assertTrue('experiment' not in context.facet_constraints)

        context2 = context.constrain(experiment='historical')
        self.assertTrue('experiment' in context2.facet_constraints)

    def test_negative_facet(self):
        conn = SearchConnection(self.test_service, cache=self.cache)

        context = conn.new_context(project='CMIP5', model='IPSL-CM5A-LR')
        hits1 = context.hit_count

        print((context.facet_counts['experiment']))

        context2 = context.constrain(experiment='historical')
        hits2 = context2.hit_count

        context3 = context.constrain(experiment=not_equals('historical'))
        hits3 = context3.hit_count

        assert hits1 == hits2 + hits3

    def _test_replica(self, facets=None):

        # Test that we can exclude replicas
        # This tests assumes the test dataset is replicated
        conn = SearchConnection(self.test_service)
        qry = 'id:cmip5.output1.MOHC.HadGEM2-ES.rcp45.mon.atmos.Amon.r1i1p1.*'
        version = '20111128'

        # Search for all replicas
        context = conn.new_context(query=qry, version=version,
                                   facets=facets)

        # Expecting more than 2 search hits for replicas
        assert context.hit_count > 2

        # Search for only one replicant
        context = conn.new_context(query=qry, replica=False, version=version,
                                   facets=facets)
        # Expecting one search replica
        assert context.hit_count == 1

    def test_replica_with_few_facets(self):
        self._test_replica(facets=self._test_few_facets)

    @pytest.mark.xfail
    # Expected failure - same considerations as test_distrib_all_facets
    @pytest.mark.slow
    def test_replica_with_all_facets(self):
        self._test_replica()

    def test_response_from_bad_parameter(self):
        # Test that a bad parameter name raises a useful exception
        # NOTE::: !!! This would fail because urllib2 HTTP query is overridden
        #         !!! with
        #         !!! cache handler instead of usual response.
        #         !!! So catch other error instead

        conn = SearchConnection(self.test_service, cache=self.cache)
        context = conn.new_context(project='CMIP5', rubbish='nonsense')

        try:
            context.hit_count
        except Exception as err:
            self.assertTrue(str(err).strip() in (
                "Invalid query parameter(s): rubbish",
                "No JSON object could be decoded"))

    @pytest.mark.slow
    def test_context_project_cmip6(self):
        test_service = 'https://esgf-node.llnl.gov/esg-search'
        conn = SearchConnection(test_service)

        context = conn.new_context(project='CMIP6', institution_id='AWI', distrib=False)
        self.assertTrue(context.hit_count > 100)

        context2 = context.constrain(variable='tas')
        self.assertTrue(context2.hit_count > 10)
