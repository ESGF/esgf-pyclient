"""

Module :mod:`pyesgf.logon`
==========================

Manage the client's interaction with ESGF's security system.  Using this
module requires installing the MyProxyClient_ library.

.. _MyProxyClient: http://pypi.python.org/pypi/MyProxyClient

To obtain ESGF credentials create a :class:`LogonManager` instance and supply
it with logon details::

  >>> lm = LogonManager()
  >>> lm.is_logged_on()
  False
  >>> lm.logon(username, password, myproxy_hostname, bootstrap=True)
  >>> lm.is_logged_on()
  True

Logon parameters that aren't specified will be prompted for at the terminal
by default.  The :class:`LogonManager` object also writes a ``.httprc`` file
configuring OPeNDAP access through the NetCDF API.

The option ``bootstrap=True`` is needed on the first run.

You can use your OpenID to logon instead.  The logon details will be deduced
from the OpenID where possible::

  >>> lm.logoff()
  >>> lm.is_logged_on()
  False
  >>> lm.logon_with_openid(openid, password, bootstrap=True)
  >>> lm.is_logged_on()
  True

"""

import os
import os.path as op
import shutil
from defusedxml import ElementTree
import requests
import re
from getpass import getpass

try:
    from myproxy.client import MyProxyClient
    import OpenSSL
    _has_myproxy = True
except (ImportError, SyntaxError):
    _has_myproxy = False

from .exceptions import OpenidResolutionError

# -----------------------------------------------------------------------------
# Constants

ESGF_DIR = op.join(os.path.expanduser('~'), '.esg')
ESGF_CERTS_DIR = 'certificates'
ESGF_CREDENTIALS = 'credentials.pem'
DAP_CONFIG = op.join(os.path.expanduser('~'), '.dodsrc')
DAP_CONFIG_MARKER = '<<< Managed by esgf-pyclient >>>'

XRI_NS = 'xri://$xrd*($v*2.0)'
MYPROXY_URN = 'urn:esg:security:myproxy-service'
ESGF_OPENID_REXP = r'https://.*/esgf-idp/openid/(.*)'
MYPROXY_URI_REXP = r'socket://([^:]*):?(\d+)?'

# -----------------------------------------------------------------------------
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

    def __init__(self, esgf_dir=ESGF_DIR, dap_config=DAP_CONFIG,
                 verify=True):
        """
        :param esgf_dir: Root directory of ESGF state.  Default ~/.esg
        :param dap_config: Set the location of .httprc.  Defaults to ~/.httprc
        :param verify: SSL verification option. Default ``True``.

        See the ``requests`` documenation to configure the
        ``verify`` option:

        http://docs.python-requests.org/en/master/user/advanced/#ssl-cert-verification

        Note if dap_config is defined your current working directory must be
        the same as the location as the dap_config file when OPeNDAP is
        initialised.
        """
        if not _has_myproxy:
            raise ImportError('pyesgf.logon requires MyProxyClient')

        self.esgf_dir = esgf_dir
        self.esgf_credentials = op.join(self.esgf_dir, ESGF_CREDENTIALS)
        self.esgf_certs_dir = op.join(self.esgf_dir, ESGF_CERTS_DIR)
        self.dap_config = dap_config
        self.verify = verify

        self._write_dap_config()

    @property
    def state(self):
        if not op.exists(self.esgf_credentials):
            return self.STATE_NO_CREDENTIALS
        else:
            with open(self.esgf_credentials) as fh:
                data = fh.read()
                cert = OpenSSL.crypto.load_certificate(
                    OpenSSL.SSL.FILETYPE_PEM, data)

            if cert.has_expired():
                return self.STATE_EXPIRED_CREDENTIALS

            # !TODO: check credentials against certificates

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
                print('Enter myproxy hostname:', end=' ')
                hostname = input()
            if username is None:
                print('Enter myproxy username:', end=' ')
                username = input()
            if password is None:
                password = getpass('Enter password for %s: ' % username)

        if None in (hostname, username, password):
            raise OpenidResolutionError('Full logon details not available')

        c = MyProxyClient(hostname=hostname, caCertDir=self.esgf_certs_dir)

        creds = c.logon(username, password,
                        bootstrap=bootstrap,
                        updateTrustRoots=update_trustroots)
        with open(self.esgf_credentials, 'wb') as fh:
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
        response = requests.get(openid, verify=self.verify)
        xml = ElementTree.fromstring(response.content)

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

        # !TODO maybe support different myproxy port
        if port is not None:
            if not int(port) == 7512:
                raise AssertionError()

        return username, hostname

    def _write_dap_config(self, verbose=False, validate=False):
        preamble, managed, postamble = self._parse_dap_config()

        with open(self.dap_config, 'w') as fh:
            fh.write(('{preamble}\n'
                      '# BEGIN {marker}\n'
                      'HTTP.VERBOSE={verbose}\n'
                      'HTTP.COOKIEJAR={esgf_dir}/.dods_cookies\n'
                      'HTTP.SSL.VALIDATE=0\n'
                      'HTTP.SSL.CERTIFICATE={esgf_dir}/credentials.pem\n'
                      'HTTP.SSL.KEY={esgf_dir}/credentials.pem\n'
                      'HTTP.SSL.CAPATH={esgf_certs_dir}\n'
                      '# END {marker}\n'
                      '{postamble}\n')
                     .format(verbose=1 if verbose else 0,
                             # validate=1 if validate else 0,
                             esgf_certs_dir=self.esgf_certs_dir,
                             esgf_dir=self.esgf_dir,
                             marker=DAP_CONFIG_MARKER,
                             preamble=preamble,
                             postamble=postamble))

    def _parse_dap_config(self, config_str=None):
        """
        Read the DAP_CONFIG file and extract the parts not controlled
        by esgf-pyclient.

        :return: (preamble, managed, postamble), three strings of
            configuration lines before, within and after the esgf-pyclient
            controlled block.

        """
        if config_str is None:
            if not op.exists(self.dap_config):
                return ('', '', '')
            config_str = open(self.dap_config).read()

        sections = re.split(r'^# (?:BEGIN|END) {0}$\n'
                            .format(DAP_CONFIG_MARKER),
                            config_str, re.M)

        if len(sections) < 2:
            preamble, managed, postamble = sections[0], '', ''
        elif len(sections) == 2:
            preamble, managed, postamble = sections + ['']
        elif len(sections) == 3:
            preamble, managed, postamble = sections
        else:
            # In odd circumstances there might be more than 3 parts of the
            # config so assume the final config is the one to keep
            managed, unmanaged = [], []
            sections.reverse()
            while sections:
                unmanaged.append(sections.pop())
                if sections:
                    managed.append(sections.pop())

            preamble = '\n'.join(unmanaged[:-1])
            postamble = unmanaged[-1]
            managed = managed[-1]

        return preamble.strip(), managed.strip(), postamble.strip()
