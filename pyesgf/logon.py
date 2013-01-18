"""

Module :mod:`pyesgf.logon`
==========================

Manage the client's interaction with ESGF's security system.  Using this module requires installing the MyProxyClient_ library.

.. _MyProxyClient: http://pypi.python.org/pypi/MyProxyClient

To obtain ESGF credentials create a :class:`LogonManager` instance and supply it with logon
details::

  >>> lm = LogonManager()
  >>> lm.is_logged_on()
  False
  >>> lm.logon(username, password, myproxy_hostname)
  >>> lm.is_logged_on()
  True

Logon parameters that aren't specified will be prompted for at the terminal
by default.  The :class:`LogonManager` object also writes a ``.httprc`` file configuring
OPeNDAP access through the NetCDF API.

You can use your OpenID to logon instead.  The logon details will be deduced
from the OpenID where possible::

  >>> lm.logoff()
  >>> lm.is_logged_on()
  False
  >>> lm.logon_with_openid(openid, password)
  >>> lm.is_logged_on()
  True

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
    _has_myproxy = True
except ImportError:
    _has_myproxy = False

from .exceptions import OpenidResolutionError

#-----------------------------------------------------------------------------
# Constants

ESGF_DIR = op.join(os.environ['HOME'], '.esg')
ESGF_CERTS_DIR = 'certificates'
ESGF_CREDENTIALS = 'credentials.pem'
DAP_CONFIG = op.join(os.environ['HOME'], '.httprc')

XRI_NS = 'xri://$xrd*($v*2.0)'
MYPROXY_URN = 'urn:esg:security:myproxy-service'
ESGF_OPENID_REXP = r'https://.*/esgf-idp/openid/(.*)'
MYPROXY_URI_REXP = r'socket://([^:]*):?(\d+)?'

#-----------------------------------------------------------------------------
# classes

class LogonManager(object):
    """
    Manages ESGF crendentials and security configuration files.

    Also integrates with NetCDF's secure OPeNDAP configuration.
    
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
        if not _has_myproxy:
            raise ImportError('pyesgf.logon requires MyProxyClient')

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
                          bootstrap=False, update_trustroots=True,
                          interactive=True):
        """
        Obtains ESGF credentials by detecting the MyProxy parameters from
        the users OpenID.  Some ESGF compatible OpenIDs do not contain enough
        information to obtain credentials.  In this case the user is prompted
        for missing information if ``interactive == True``, otherwise an
        exception is raised.

        :param openid: OpenID to login with See :meth:`logon` for parameters
            ``interactive``, ``bootstrap`` and ``update_trustroots``.
        """
        username, myproxy = self._get_logon_details(openid)
        return self.logon(username, password, myproxy,
                          bootstrap=bootstrap,
                          update_trustroots=update_trustroots,
                          interactive=interactive)


    def logon(self, username=None, password=None, hostname=None,
              bootstrap=False, update_trustroots=True,
              interactive=True):
        """
        Obtain ESGF credentials from the specified MyProxy service.

        If ``interactive == True`` then any missing parameters of ``password``,
        ``username`` or ``hostname`` will be prompted for at the terminal.
        
        :param interactive: Whether to ask for input at the terminal for
            any missing information.  I.e. username, password or hostname.
        :param bootstrap: Whether to bootstrap the trustroots for this
            MyProxy service.
        :param update_trustroots: Whether to update the trustroots for this
            MyProxy service.

        """
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
        """
        Remove any obtained credentials from the ESGF environment.
        
        :param clear_trustroots: If True also remove trustroots.
    
        """
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
