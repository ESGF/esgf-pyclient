# Install cache for faster access

import os

from .cache_urllib2 import install_cache
from .config import CACHE_DIR

install_cache(os.path.join(os.path.dirname(__file__), CACHE_DIR))
