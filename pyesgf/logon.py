"""

Module :mod:`pyesgf.logon`
==========================

Manage the client's interaction with esg-security

"""

import os
import os.path as op
import datetime

try:
    from myproxy.client import MyProxyClient
except ImportError:
    raise ImportError('pyesgf.logon requires MyProxyClient')

#-----------------------------------------------------------------------------
# Constants

ESGF_DIR = op.join(os.environ['HOME'], '.esg')
ESGF_CERTS_DIR = op.join(ESGF_DIR, 'certificates')
ESGF_CREDENTIALS = op.join(ESGF_DIR, 'credentials.pem')
#!TODO: support .httprc as well
DAP_CONFIG = op.join(os.environ['HOME'], '.dodsrc')

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

    def __init__(self, openid):
        self.openid=openid
        
        username, myproxy = cls._get_logon_details()
        self.username = username
        self.myproxy = myproxy

        self._write_dap_config()

    @property
    def state(self):
        if not op.exists(ESGF_CREDENTIALS):
            return self.STATE_NO_CREDENTIALS
        else:
            with open(ESGF_CREDENTIALS) as fh:
                data = fh.read()
                cert = OpenSSL.cryto.load_certificate(OpenSSL.SSL.FILETYPE_PEM, data)

            if cert.has_expired():
                return self.STATE_EXPIRED_CREDENTIALS

            #!TODO: check credentials against certificates

            return self.STATE_LOGGED_ON

    def is_logged_on(self):
        return self.state == self.STATE_LOGGED_ON

    def logon(self, password=None, bootstrap=False, update_trustroots=False):
        if password is None:
            password = getpass('Enter password for %s: ' % self.open_id)

        c = MyProxyClient(hostname=self.myproxy, caCertDir=ESGF_CERT_DIR)

        c.logon(self.username, self.password,
                boostrap=bootstrap, updateTrustRoots=update_trustroots,
                sslCertFile=ESGF_CERTS_DIR, sslKeyFile=ESGF_CREDENTIALS)

    def _get_logon_details(self):
        raise NotImplementedError

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
""".format(1 if verbose else 0, ESGF_DIR)
