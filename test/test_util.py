"""
Test pyesgf.util module.

"""

from pyesgf.search.connection import SearchConnection
from pyesgf.util import get_manifest

#!TODO: Make this one of the test services.
CEDA_SERVICE = 'http://esgf-index1.ceda.ac.uk/esg-search/search'

def test_get_manifest():
    conn = SearchConnection(CEDA_SERVICE, distrib=False)

    manifest = get_manifest('GeoMIP.output1.MOHC.HadGEM2-ES.G1.day.atmos.day.r1i1p1',
                         20120223, conn)

    filename = 'psl_day_HadGEM2-ES_G1_r1i1p1_19291201-19291230.nc'
    assert manifest[filename]['checksum'] == 'd20bbba8e05d6689f44cf3f8eebb9e7b'
