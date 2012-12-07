"""

Module :mod:`pyesgf.logon`
==========================

Manage the client's interaction with esg-security

"""

import os
import os.path as op
import datetime
import shutil
from xml.etree import ElementTree
import urllib2
import re

try:
    from myproxy.client import MyProxyClient
    import OpenSSL
except ImportError:
    raise ImportError('pyesgf.logon requires MyProxyClient')

from .exceptions import OpenidResolutionError

#-----------------------------------------------------------------------------
# Constants

ESGF_DIR = op.join(os.environ['HOME'], '.esg')
ESGF_CERTS_DIR = 'certificates'
ESGF_CREDENTIALS = 'credentials.pem'
#!TODO: support .httprc as well
DAP_CONFIG = op.join(os.environ['HOME'], '.httprc')

XRI_NS = 'xri://$xrd*($v*2.0)'
MYPROXY_URN = 'urn:esg:security:myproxy-service'
ESGF_OPENID_REXP = r'https://.*/esgf-idp/openid/(.*)'
MYPROXY_URI_REXP = r'socket://([^:]*):?(\d+)?'

#-----------------------------------------------------------------------------
# classes

class LogonManager(object):
    """
    Manages ESGF crendentials and security config files.
    
    """
    STATE_LOGGED_ON = 0
    STATE_NO_CREDENTIALS = 1
    STATE_EXPIRED_CREDENTIALS = 2
    STATE_INVALID_CREDENTIALS = 3

    def __init__(self, esgf_dir=ESGF_DIR, dap_config=DAP_CONFIG):
        """
        :param esgf_dir: Root directory of ESGF state.  Default ~/.esg
        :param dap_config: Set the location of .httprc.  Defaults to ~/.httprc

        Note if dap_config is defined your current working directory must be the
        same as the location as the dap_config file when OPeNDAP is initiallised.

        """
        
        self.esgf_dir = esgf_dir
        self.esgf_credentials = op.join(self.esgf_dir, ESGF_CREDENTIALS)
        self.esgf_certs_dir = op.join(self.esgf_dir, ESGF_CERTS_DIR)
        self.dap_config = dap_config

        self._write_dap_config()

    @property
    def state(self):
        if not op.exists(self.esgf_credentials):
            return self.STATE_NO_CREDENTIALS
        else:
            with open(self.esgf_credentials) as fh:
                data = fh.read()
                cert = OpenSSL.crypto.load_certificate(OpenSSL.SSL.FILETYPE_PEM, data)

            if cert.has_expired():
                return self.STATE_EXPIRED_CREDENTIALS

            #!TODO: check credentials against certificates

            return self.STATE_LOGGED_ON


    def is_logged_on(self):
        return self.state == self.STATE_LOGGED_ON


    def logon_with_openid(self, openid, password=None,
                          bootstrap=False, update_trustroots=False,
                          interactive=True):
        """
        :param openid: OpenID to login with
        :param interactive: Whether to ask for input at the terminal for
            any information that cannot be deduced from the OpenID.
        """
        username, myproxy = self._get_logon_details(openid)
        return self.logon(username, password, myproxy,
                          bootstrap=bootstrap,
                          update_trustroots=update_trustroots,
                          interactive=interactive)


    def logon(self, username=None, password=None, hostname=None,
              bootstrap=False, update_trustroots=False,
              interactive=True):
        if interactive:
            if hostname is None:
                print 'Enter myproxy hostname:',
                hostname = raw_input()
            if username is None:
                print 'Enter myproxy username:',
                username = raw_input()
            if password is None:
                password = getpass('Enter password for %s: ' % self.open_id)

        if None in (hostname, username, password):
            raise OpenidResolutionError('Full logon details not available')

        c = MyProxyClient(hostname=hostname, caCertDir=self.esgf_certs_dir)

        creds = c.logon(username, password,
                        bootstrap=bootstrap, updateTrustRoots=update_trustroots)
        with open(self.esgf_credentials, 'w') as fh:
            for cred in creds:
                fh.write(cred)
                

    def logoff(self, clear_trustroots=False):
        if op.exists(self.esgf_credentials):
            os.remove(self.esgf_credentials)

        if clear_trustroots:
            shutil.rmtree(self.esgf_certs_dir)

    def _get_logon_details(self, openid):
        openid_doc = urllib2.urlopen(openid).read()
        xml = ElementTree.fromstring(openid_doc)

        hostname = None
        port = None
        username = None

        services = xml.findall('.//{%s}Service' % XRI_NS)
        for service in services:
            try:
                service_type = service.find('{%s}Type' % XRI_NS).text
            except AttributeError:
                continue

            # Detect myproxy hostname and port
            if service_type == MYPROXY_URN:
                myproxy_uri = service.find('{%s}URI' % XRI_NS).text
                mo = re.match(MYPROXY_URI_REXP, myproxy_uri)
                if mo:
                    hostname, port = mo.groups()

        # If the OpenID matches the standard ESGF pattern assume it contains
        # the username, otherwise prompt or raise an exception
        mo = re.match(ESGF_OPENID_REXP, openid)
        if mo:
            username = mo.group(1)
                
        #!TODO maybe support different myproxy port
        if port is not None:
            assert int(port) == 7512
            
        return username, hostname
            

    def _write_dap_config(self, verbose=False):
        #!TODO: replace with more sophisticated routine that merges settings
        with open(DAP_CONFIG, 'w') as fh:
            fh.write("""\
CURL.VERBOSE={0}
CURL.COOKIEJAR={1}/.dods_cookies
CURL.SSL.VALIDATE=1
CURL.SSL.CERTIFICATE={1}/credentials.pem
CURL.SSL.KEY={1}/credentials.pem
CURL.SSL.CAPATH={1}/certificates
""".format(1 if verbose else 0, self.esgf_certs_dir))
