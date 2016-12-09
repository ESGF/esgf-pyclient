
Examples of :mod:`pyesgf.search` usage
======================================

Prelude

::

  >>> from pyesgf.search import SearchConnection
  >>> conn = SearchConnection('http://pcmdi9.llnl.gov/esg-search',
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

Find download URLs for all files in a dataset::

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

Define a search for datasets that includes a temporal range::

  >>> conn = SearchConnection('http://esgf-index1.ceda.ac.uk/esg-search',
                        distrib=False)
  >>> ctx = conn.new_context(project = "CMIP5", model = "HadGEM2-ES",
          time_frequency = "mon", realm = "atmos", ensemble = "r1i1p1", latest = True,
          from_timestamp = "2100-12-30T23:23:59Z", to_timestamp = "2200-01-01T00:00:00Z")
  >>> ctx.hit_count
  3

Or do the same thing by searching without temporal constraints and then applying the constraint::

  >>> ctx = conn.new_context(project = "CMIP5", model = "HadGEM2-ES",
          time_frequency = "mon", realm = "atmos", ensemble = "r1i1p1", latest = True)
  >>> ctx.hit_count
  21
  >>> ctx = ctx.constrain(from_timestamp = "2100-12-30T23:23:59Z", to_timestamp = "2200-01-01T00:00:00Z")
  >>> ctx.hit_count
  3

Obtain MyProxy credentials to allow downloading files or using secured OPeNDAP::

  >>> from pyesgf.logon import LogonManager
  >>> lm = LogonManager()
  >>> lm.logoff()
  >>> lm.is_logged_on()
  False
  >>> lm.logon_with_openid(openid, password)
  >>> lm.is_logged_on()
  True

NOTE: you may be prompted for your username if not available via your OpenID.

Obtain MyProxy credentials from your username, password and the MyProxy host::

  >>> myproxy_host = 'slcs1.ceda.ac.uk'
  >>> lm.logon(userid, password, myproxy_host)
  >>> lm.is_logged_on()
  True

See the :mod:`pyesgf.logon` module documentation for details of how to use myproxy username instead of OpenID.

Now download a file using the ESGF wget script extracted from the server::

  >>> fc = ds.file_context()
  >>> wget_script_content = fc.get_download_script()
  >>> script_name = 'download.sh'
  >>> with open(script_name, "w") as writer: 
  ...    writer.write(wget_script_content)
  ...
  >>> import os, commands
  >>> os.chmod(script_name, 0750)
  >>> commands.getoutput("./%s" % script_name)

...and the files will be downloaded to the current directory.

If you are doing batch searching and things are running slow, you might be able to 
achieve a considerable speed up by sending the following argument to the search call::

  >>> ctx.search(ignore_facet_check=True)

This cuts out an extra call that typically takes 2 seconds to return a response. Note that 
it may mean some of the functionality is affected (such as being able to view the available
facets and access the hit count) so use this feature with care.

You can also dictate how the search batches up its requests with:

  >>> ctx.search(batch_size=250)

The `batch_size` argument does not affect the final result but may affect the speed of the response. 
The batch size can also be set as a default in the :mod:`pyesgf.search.consts` module.

