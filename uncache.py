#!/usr/bin/env python

import sys

from test.config import CACHE_DIR
from test.cache_urllib2 import remove_from_cache

full_cache_dir = 'test/%s' % CACHE_DIR

if __name__ == '__main__':
    urls = sys.argv[1:]

    for url in urls:
        print('Removing %s' % url)
        remove_from_cache(url, full_cache_dir)
