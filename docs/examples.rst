
Examples of :mod:`pyesgf.search` usage
======================================

Prelude

::

  >>> from pyesgf.search import SearchConnection
  >>> conn = SearchConnection('http://pcmdi9.llnl.gov/esg-search/search',
  ...                         distrib=True)

Find how many datasets containing 'humidity' in a given experiment family::

  >>> ctx = conn.new_context(project='CMIP5', query='humidity')
  >>> ctx.hit_count
  20372
  >>> ctx.facet_counts['experiment_family']
  {u'All': 20372, u'Atmos-only': 1658, u'Control': 493, u'Decadal': 12922, u'ESM': 410, u'Historical': 2292, u'Idealized': 982, u'Paleo': 125, u'RCP': 1927}


Find the OPeNDAP URL for an aggregated dataset::

  >>>  ctx = conn.new_context(project='CMIP5', model='HadCM3', experiment='decadal2000', time_frequency='day')
  >>> print 'Hits:', ctx.hit_count
  >>> print 'Realms:', ctx.facet_counts['realm']
  >>> print 'Ensembles:', ctx.facet_counts['ensemble']
  Hits: 40
  Realms: {u'atmos': 20, u'ocean': 20}
  Ensembles: {u'r4i2p1': 2, u'r2i2p1': 2, u'r5i2p1': 2, u'r10i2p1': 2, u'r3i2p1': 2, u'r9i2p1': 2, u'r7i2p1': 2, u'r5i3p1': 2, u'r8i3p1': 2, u'r3i3p1': 2, u'r6i3p1': 2, u'r9i3p1': 2, u'r1i2p1': 2, u'r7i3p1': 2, u'r8i2p1': 2, u'r6i2p1': 2, u'r4i3p1': 2, u'r1i3p1': 2, u'r10i3p1': 2, u'r2i3p1': 2}
  >>> ctx = ctx.constrain(realm='ocean', ensemble='r1i2p1')
  >>> ctx.hit_count
  1
  >>> result = ctx.search()[0]
  >>> agg_ctx = result.aggregation_context()
  >>> agg = agg_ctx.search()[0]
  >>> print agg.opendap_url
  http://cmip-dn1.badc.rl.ac.uk/thredds/dodsC/cmip5.output1.MOHC.HadCM3.decadal2000.day.ocean.day.r1i2p1.tos.20110708.aggregation.1

Find download URLs for all files in a dataset

  >>> ctx = conn.new_context(project='obs4MIPs', model='Obs-TES')
  >>> ctx.hit_count
  1
  >>> ds = ctx.search()[0]
  >>> files = ds.file_context().search()
  >>> len(files)
  3
  >>> for f in files:
  ...     print f.download_url
  http://esg-datanode.jpl.nasa.gov/thredds/fileServer/esg_dataroot/obs4MIPs/observations/atmos/tro3Nobs/mon/grid/NASA-JPL/TES/v20110608/tro3Nobs_TES_L3_tbd_200507-200912.nc
  http://esg-datanode.jpl.nasa.gov/thredds/fileServer/esg_dataroot/obs4MIPs/observations/atmos/tro3/mon/grid/NASA-JPL/TES/v20110608/tro3_TES_L3_tbd_200507-200912.nc
  http://esg-datanode.jpl.nasa.gov/thredds/fileServer/esg_dataroot/obs4MIPs/observations/atmos/tro3Stderr/mon/grid/NASA-JPL/TES/v20110608/tro3Stderr_TES_L3_tbd_200507-200912.nc
