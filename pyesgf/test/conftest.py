# Install cache for faster access

import os

#import pyesgf
from pyesgf.cache_urllib2 import install_cache

import pytest
CACHE_DIR = 'url_cache'
CACHE_DIR = os.path.join(os.path.dirname(__file__), CACHE_DIR)


@pytest.fixture(scope="session", autouse=True)
def cache_dir():
    install_cache(CACHE_DIR)
    return CACHE_DIR


@pytest.fixture(scope="session")
def TEST_SERVICE():
    return 'http://esgf-index1.ceda.ac.uk/esg-search'
