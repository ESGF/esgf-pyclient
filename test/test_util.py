"""
Test pyesgf.util module.

"""

import re

from pyesgf.search.connection import SearchConnection
from pyesgf.util import get_manifest

#!TODO: Make this one of the test services.
CEDA_SERVICE = 'http://esgf-index1.ceda.ac.uk/esg-search'

def test_get_manifest():
    conn = SearchConnection(CEDA_SERVICE, distrib=False)

    manifest = get_manifest('GeoMIP.output1.MOHC.HadGEM2-ES.G1.day.atmos.day.r1i1p1',
                         20120223, conn)

    filename = 'psl_day_HadGEM2-ES_G1_r1i1p1_19291201-19291230.nc'
    assert manifest[filename]['checksum'] == 'd20bbba8e05d6689f44cf3f8eebb9e7b'

#!TODO: this test belongs somewhere else
def test_opendap_url():
    conn = SearchConnection(CEDA_SERVICE, distrib=False)

    ctx = conn.new_context()
    results = ctx.search(drs_id='GeoMIP.output1.MOHC.HadGEM2-ES.G1.day.atmos.day.r1i1p1')
    assert len(results) == 1

    agg_ctx = results[0].aggregation_context()
    aggs = agg_ctx.search()

    # Take first aggregation
    agg = aggs[0]
     
    print agg.aggregation_id
    print agg.json['cf_standard_name']
    print agg.urls

    opendap_url = agg.opendap_url
    print opendap_url

def test_download_url():
    conn = SearchConnection(CEDA_SERVICE, distrib=False)

    ctx = conn.new_context()
    results = ctx.search(drs_id='GeoMIP.output1.MOHC.HadGEM2-ES.G1.day.atmos.day.r1i1p1')
    files = results[0].file_context().search()

    download_url = files[0].download_url
    assert re.match(r'http://.*\.nc', download_url)
    

def test_opendap_fail():
    conn = SearchConnection(CEDA_SERVICE, distrib=False)

    ctx = conn.new_context()
    results = ctx.search(project='CMIP5', experiment='rcp45', time_frequency='mon',
                         realm='atmos', ensemble='r1i1p1')

    files_ctx = results[0].file_context()
    hit = files_ctx.search()[0]

    assert hit.opendap_url is None
