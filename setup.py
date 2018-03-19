# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

from setuptools import setup, find_packages
import sys
import os

# Import version from the top-level package
from pyesgf import __version__
from pyesgf import __doc__ as long_description
sys.path[:0] = os.path.dirname(__file__)

setup(name='esgf-pyclient',
      version=__version__,
      description="A library interacting with ESGF services within Python",
      long_description=long_description,
      classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: BSD License',
        'Topic :: Scientific/Engineering',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'
        ],
      # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Ag Stephens',
      author_email='Ag.Stephens@stfc.ac.uk',
      url='http://esgf-pyclient.readthedocs.org',
      download_url='https://github.com/ESGF/esgf-pyclient',
      license='BSD',
      packages=find_packages(exclude=['ez_setup', 'examples', 'test']),
      include_package_data=True,
      zip_safe=False,
      install_requires=['jinja2', 'requests', 'requests_cache', 'six'],
      extras_require={'testing':
                      ['myproxyclient', 'pytest', 'nose', 'flake8']},
      tests_require=['pytest', 'flake8'],
      entry_points={},
      test_suite='test')
