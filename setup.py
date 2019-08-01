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

reqs = [line.strip() for line in open('requirements.txt')]
dev_reqs = [line.strip() for line in open('requirements_dev.txt')]

setup(name='esgf-pyclient',
      version=__version__,
      description="A library interacting with ESGF services within Python",
      long_description=long_description,
      classifiers=[
          'Development Status :: 4 - Beta',
          'License :: OSI Approved :: BSD License',
          'Topic :: Scientific/Engineering',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
      ],
      # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Ag Stephens',
      author_email='Ag.Stephens@stfc.ac.uk',
      url='http://esgf-pyclient.readthedocs.org',
      download_url='https://github.com/ESGF/esgf-pyclient',
      license='BSD',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=reqs,
      extras_require={
          "dev": dev_reqs,              # pip install ".[dev]"
      },
      entry_points={},
      test_suite='test')
