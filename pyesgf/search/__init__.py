"""
An interface to the `ESGF Search API`_


.. _`ESGF Search API`: http://esgf.org/wiki/ESGF_Search_API

"""

from .connection import SearchConnection  # noqa: F401
from .context import SearchContext  # noqa: F401
from .constraints import GeospatialConstraint, any_of, not_equals  # noqa: F401
from .results import ResultSet  # noqa: F401
from .consts import TYPE_DATASET, TYPE_FILE  # noqa: F401

# !TODO: ResultFormatter class.  process response json to specialise the result
#        json.  Default is None
# !TODO: pipe results to new process.  Command-line interface.
