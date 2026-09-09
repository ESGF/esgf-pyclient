[![Documentation Status](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://esgf-pyclient.readthedocs.io/en/latest/?badge=latest)
[![Build Status](https://github.com/ESGF/esgf-pyclient/workflows/build%20%E2%9A%99%EF%B8%8F/badge.svg)](https://github.com/ESGF/esgf-pyclient/actions)
[![GitHub license](https://img.shields.io/github/license/ESGF/esgf-pyclient.svg)](https://github.com/ESGF/esgf-pyclient/blob/master/LICENSE)

# esgf-pyclient

ESGF PyClient is a Python package designed for interacting with the [Earth System Grid Federation](https://esgf.llnl.gov/) system.

> [!WARNING]
> This package interacts with the
> [legacy ESGF Search API](https://esgf.github.io/esg-search/ESGF_Search_RESTful_API.html),
> which is deprecated and servers may be shut down permanently.
> Users are encouraged to switch to
> [intake-esgf](https://intake-esgf.readthedocs.io/), or use
> [pystac-client](https://pystac-client.readthedocs.io/) to interact with the
> new STAC-based search API. The new STAC servers are available at:
> 
> - https://discovery.east.esgf.io
> - https://discovery.west.esgf.io
>
> Progress reports on the development of the new ESGF infrastructure can
> be found on the [ESGF Roadmap GitHub
> repository](https://github.com/ESGF/esgf-roadmap/blob/main/status/README.md).

This package contains API code for calling the
[legacy ESGF Search API](https://esgf.github.io/esg-search/ESGF_Search_RESTful_API.html)
from Python code. It may be used to access data that is only findable
through the legacy ESGF Search API, such as CMIP5, CORDEX, and older
obs4MIPs data.

You can try it online using Binder, or view the notebooks on NBViewer:
[![Binder Launcher](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/ESGF/esgf-pyclient.git/master?filepath=notebooks)
[![NBViewer](https://raw.githubusercontent.com/jupyter/design/master/logos/Badges/nbviewer_badge.svg)](https://nbviewer.jupyter.org/github/ESGF/esgf-pyclient/tree/master/notebooks/)

Please submit bugs and feature requests through the bug tracker on
[GitHub](https://github.com/ESGF/esgf-pyclient). Pull requests are
always welcome.

Full [documentation](http://esgf-pyclient.readthedocs.org) is available
on ReadTheDocs or in the docs directory.

## Available servers

At the time of writing (September 9, 2026), servers providing search
using this API may be found at the following URLs:

- <https://esgf-node.ornl.gov/esgf-1-5-bridge> (partially supports the legacy ESGF Search API, issues can be reported [here](https://github.com/esgf2-us/esg_fastapi/issues))
- <https://esgf.ceda.ac.uk/esg-search/search>
- <https://esgf-data.dkrz.de/esg-search/search>
- <https://esg-dn1.nsc.liu.se/esg-search/search>

while the following servers appear to be online, but return an error
page:

- <https://esgf-node.ipsl.upmc.fr/esg-search/search>
- <https://esgf.nci.org.au/esg-search/search>
- <https://esgf.nccs.nasa.gov/esg-search/search>
- <https://esgdata.gfdl.noaa.gov/esg-search/search>

Note that logging in using OpenID with the
[`pyesgf.logon`](https://esgf-pyclient.readthedocs.io/en/latest/api.html#module-pyesgf-logon)
module is no longer required to access ESGF data.
All servers supporting this feature have been taken offline.
