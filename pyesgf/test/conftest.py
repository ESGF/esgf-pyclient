# Install cache for faster access

import os
from pyesgf.cache_urllib2 import install_cache
import six

import pytest
CACHE_DIR = 'url_cache'
CACHE_DIR = os.path.join(os.path.dirname(__file__), CACHE_DIR)


@pytest.fixture(scope="session", autouse=True)
def cache_dir():
    if six.PY2:
        # The Cache currently only work in Python 2.
        # There appears to be a bug in Python 3 io.StringIO
        # that prevents easy migration.
        install_cache(CACHE_DIR)
    return CACHE_DIR
