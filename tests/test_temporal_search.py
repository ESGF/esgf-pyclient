"""
test_temporal_search.py
=======================

Uses CMIP5 to find HadGEM2-ES dataset ids that include data
between 1960 and 1962.

Tests whether the "from_timestamp" and "to_timestamp" options
are working in esgf-pyclient.

"""

from pyesgf.search import SearchConnection
from unittest import TestCase


class TestTemporalSearch(TestCase):
    def setUp(self):
        self.test_service1 = 'https://esgf.ceda.ac.uk/esg-search'
        self.test_service2 = "http://esgf-data.dkrz.de/esg-search"

    def test_temporal_search_CMIP5(self):
        conn = SearchConnection(self.test_service1, distrib=False)

        ctx1 = conn.new_context(
                    project="CMIP5", model="HadGEM2-ES",
                    time_frequency="mon", realm="atmos",
                    ensemble="r1i1p1", latest=True)

        ctx2 = conn.new_context(
                  project="CMIP5", model="HadGEM2-ES",
                  time_frequency="mon", realm="atmos",
                  ensemble="r1i1p1", latest=True,
                  from_timestamp="2100-12-30T23:23:59Z",
                  to_timestamp="2200-01-01T00:00:00Z")

        assert ctx2.hit_count < ctx1.hit_count

    def test_temporal_search_CORDEX(self):
        conn = SearchConnection(self.test_service2, distrib=True)

        ctx1 = conn.new_context(project='CORDEX',
                                from_timestamp="1990-01-01T12:00:00Z",
                                to_timestamp="2100-12-31T12:00:00Z")

        ctx2 = conn.new_context(project='CORDEX',
                                from_timestamp="2011-01-01T12:00:00Z",
                                to_timestamp="2100-12-31T12:00:00Z")

        assert ctx2.hit_count < ctx1.hit_count
