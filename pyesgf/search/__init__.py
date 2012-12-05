"""
An interface to the `ESGF Search API`_


.. _`ESGF Search API`: http://esgf.org/wiki/ESGF_Search_API

"""

from .connection import SearchConnection
from .context import SearchContext
from .constraints import GeospatialConstraint, any_of, not_equals
from .results import ResultSet
from .consts import TYPE_DATASET, TYPE_FILE


#!TODO: ResultFormatter class.  process response json to specialise the result json.  Default is None
#!TODO: pipe results to new process.  Command-line interface.

    
    

    
