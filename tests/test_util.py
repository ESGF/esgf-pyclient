"""
Test pyesgf.util module.

"""

import pytest

import re

from pyesgf.search.connection import SearchConnection
from pyesgf.util import get_manifest, ats_url
from unittest import TestCase


class TestUtil(TestCase):
    def setUp(self):
        # !TODO: Make this one of the test services.
        self.test_service = 'https://esgf.ceda.ac.uk/esg-search'

    def test_ats_url(self):
        assert ats_url('https://esgf-node.llnl.gov') == 'https://esgf-node.llnl.gov/esgf-idp/saml/soap/secure/attributeService.htm'  # noqa

    @pytest.mark.slow
    def test_get_manifest(self):
        conn = SearchConnection(self.test_service, distrib=False)

        manifest = get_manifest('GeoMIP.output.MOHC.HadGEM2-ES.G1.day.'
                                'atmos.day.r1i1p1',
                                20120223, conn)

        filename = 'psl_day_HadGEM2-ES_G1_r1i1p1_19291201-19291230.nc'
        assert manifest[filename]['checksum'] == ('5c459a61cfb904ca235ad1f79'
                                                  '6227114df095d9162a2a3f044'
                                                  'bc01f881b532ce')

    # !TODO: this test belongs somewhere else
    def test_opendap_url(self):
        conn = SearchConnection(self.test_service, distrib=False)

        ctx = conn.new_context()
        results = ctx.search(drs_id=('GeoMIP.output.MOHC.HadGEM2-ES.G1.'
                                     'day.atmos.day.r1i1p1'))
        assert len(results) == 1

        agg_ctx = results[0].aggregation_context()
        aggs = agg_ctx.search()

        # Take first aggregation
        agg = aggs[0]

        print((agg.aggregation_id))
        print((agg.json['cf_standard_name']))
        print((agg.urls))

        opendap_url = agg.opendap_url
        print(opendap_url)

    @pytest.mark.slow
    def test_download_url(self):
        conn = SearchConnection(self.test_service, distrib=False)

        ctx = conn.new_context()
        results = ctx.search(drs_id=('GeoMIP.output.MOHC.HadGEM2-ES.G1.day.'
                                     'atmos.day.r1i1p1'))
        files = results[0].file_context().search()

        download_url = files[0].download_url
        assert re.match(r'http://.*\.nc', download_url)
