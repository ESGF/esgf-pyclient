"""
test_temporal_search.py
=======================

Uses CMIP5 to find HadGEM2-ES dataset ids that include data between 1960 and 1962.

Tests whether the "from_timestamp" and "to_timestamp" options are working in esgf-pyclient. 

"""

import os
os.environ["http_proxy"] = "http://wwwcache.rl.ac.uk:8080"
os.environ["https_proxy"] = "https://wwwcache.rl.ac.uk:8080"

from pyesgf.search import SearchConnection

conn = SearchConnection('http://esgf-index1.ceda.ac.uk/esg-search',
                        distrib=False)

ctx = conn.new_context(project = "CMIP5", model = "HadGEM2-ES")
print ctx.hit_count
ctx = ctx.constrain(time_frequency = "mon", realm = "atmos", ensemble = "r1i1p1", latest = True)
#print ctx.facet_counts
print ctx.hit_count

if 0:
    ctx = ctx.constrain(from_timestamp = "2100-12-30T23:23:59Z")
else:
    print "THINGS TO FIX:"
    
    print """   1. 400 Error - grab errors from Tomcat response that explain error.
   2. Allow DEBUG to be switched on/off. 
   3. Explain about timestamp searching in the docs.
   4. Explain that timestamp search is only for Datasets, not Files.
   5. Fix so context.constrain(**args) can take "to_timestamp" and "from_timestamp". 
"""
    ctx = conn.new_context(project = "CMIP5", model = "HadGEM2-ES",
          time_frequency = "mon", realm = "atmos", ensemble = "r1i1p1", latest = True,
          from_timestamp = "2100-12-30T23:23:59Z", to_timestamp = "2200-01-01T00:00:00Z")

print ctx.hit_count

for (i, d) in enumerate(ctx.search()):
    print "Dataset ID:", d.dataset_id
    #if i > 10: break

    for f in d.file_context().search():
        print f.filename, f.size, f.checksum
