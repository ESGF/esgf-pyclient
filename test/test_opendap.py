"""
test for secure opendap support

"""

import tempfile
import os
import os.path as op
import shutil
from unittest import TestCase
import re

from pyesgf.logon import LogonManager, DAP_CONFIG_MARKER
from pyesgf.search import SearchConnection
from test.config import TEST_SERVICE

class TestOpendap(TestCase):
    def setUp(self):
        self.esgf_dir = tempfile.mkdtemp(prefix='pyesgf_tmp')
        self.dap_config = op.join(self.esgf_dir, '.dodsrc')
        # NetCDF DAP support looks in CWD for configuration
        self.orig_dir = os.getcwd()
        os.chdir(self.esgf_dir)

    def tearDown(self):
        os.chdir(self.orig_dir)
        if op.exists(self.esgf_dir):
            shutil.rmtree(self.esgf_dir)

    def init_config(self, config):
        with open(self.dap_config, 'w') as fh:
            fh.write(config)

    def read_config(self):
        return open(self.dap_config).read()


    def check_preamble(self, preamble, config):
        return re.match((preamble + 
                         r'\s*^# BEGIN {0}'.format(DAP_CONFIG_MARKER)), 
                        config, re.M | re.S)

    def check_postamble(self, postamble, config):
        return re.search(r'^# END {0}$\s*{1}'.format(DAP_CONFIG_MARKER, postamble),
                         config, re.M | re.S)
    
    def test_config1(self):
        # Create the config file from scratch
        lm = LogonManager(self.esgf_dir, dap_config=self.dap_config)
        config = self.read_config()
        
        print config
        assert re.match(r'\s*^# BEGIN {0}$.*^# END {0}$'.format(DAP_CONFIG_MARKER),
                        config, re.M | re.S)

    def test_config2(self):
        # Create the config when one already exists.  Check it is retained.
        lines = ['# Welcome to my config file', 'SOME_OPT=foo', '']
        preamble = '\n'.join(lines)
        self.init_config(preamble)

        lm = LogonManager(self.esgf_dir, dap_config=self.dap_config)
        config = self.read_config()

        print config
        assert self.check_preamble(preamble, config)

    def test_config3(self):
        # Create the config when one already exists with the BEGIN section in it

        lines = ['# Welcome to my config file', 'SOME_OPT=foo', '']
        preamble = '\n'.join(lines)
                        
        lines = ['', '# Some more config here', 'OTHER_OPT=bar', '']
        postamble = '\n'.join(lines)

        config = '''\
{0}
# BEGIN <<< Managed by esgf-pyclient >>>
CURL.VERBOSE=0
CURL.COOKIEJAR=/tmp/foo/certificates/.dods_cookies
CURL.SSL.VALIDATE=1
CURL.SSL.CERTIFICATE=/tmp/foo/certificates/credentials.pem
CURL.SSL.KEY=/tmp/foo/certificates/credentials.pem
CURL.SSL.CAPATH=/tmp/foo/certificates/certificates
# END <<< Managed by esgf-pyclient >>>

{1}
'''.format(preamble, postamble)
                        
        self.init_config(config)

        lm = LogonManager(self.esgf_dir, dap_config=self.dap_config)
        config1 = self.read_config()
        
        print config1
        assert self.check_preamble(preamble, config1)
        assert self.check_postamble(postamble, config1)
    

    def test_open_url(self):
        import netCDF4

        lm = LogonManager(self.esgf_dir, dap_config=self.dap_config)
        print 'Using dap_config at %s' % self.dap_config

        conn = SearchConnection(TEST_SERVICE, distrib=False)

        #!TODO: replace with request for specific dataset
        ctx = conn.new_context(project='CMIP5')
        results = ctx.search()

        r1 = results[0]
        f_ctx = r1.file_context()

        file_results = f_ctx.search()
        
        opendap_url = file_results[0].opendap_url
        print 'OPeNDAP URL is %s' % opendap_url

        ds = netCDF4.Dataset(opendap_url)
        print ds.variables.keys()
    test_open_url.__test__ = False


#!TODO: more corner cases to test for in DAP_CONFIG
