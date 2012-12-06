"""

Module :mod:`pyesgf.logon`
==========================

Manage the client's interaction with esg-security

"""

import os
import os.path as op
import datetime
import shutil

try:
    from myproxy.client import MyProxyClient
    import OpenSSL
except ImportError:
    raise ImportError('pyesgf.logon requires MyProxyClient')

#-----------------------------------------------------------------------------
# Constants

ESGF_DIR = op.join(os.environ['HOME'], '.esg')
ESGF_CERTS_DIR = 'certificates'
ESGF_CREDENTIALS = 'credentials.pem'
#!TODO: support .httprc as well
DAP_CONFIG = op.join(os.environ['HOME'], '.httprc')

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

    def logon_with_openid(self, openid,
                          bootstrap=False, update_trustroots=False):
        username, myproxy = self._get_logon_details(openid)
        return self.logon(username, myproxy, bootstrap, update_trustroots)

    def logon(self, username=None, password=None, myproxy=None,
              bootstrap=False, update_trustroots=False):
        if password is None:
            password = getpass('Enter password for %s: ' % self.open_id)

        c = MyProxyClient(hostname=myproxy, caCertDir=self.esgf_certs_dir)

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
""".format(1 if verbose else 0, self.esgf_certs_dir))
