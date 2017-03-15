"""
tests for pyesgf.logon module.

"""

import tempfile
import os
import os.path as op
import shutil

from pyesgf.logon import LogonManager, ESGF_CREDENTIALS
import pytest
from unittest import TestCase
try:
    from myproxy.client import MyProxyClient
    _has_myproxy = True
except (ImportError, SyntaxError):
    _has_myproxy = False

TEST_USER = os.environ.get('USERNAME')
TEST_PASSWORD = os.environ.get('PASSWORD')
TEST_OPENID = os.environ.get('OPENID')
TEST_MYPROXY = 'slcs1.ceda.ac.uk'

TEST_DATA_DIR = op.join(op.dirname(__file__), 'data')

if None in [TEST_USER, TEST_PASSWORD, TEST_OPENID]:
    _has_login_info = False
else:
    _has_login_info = True


def _load_creds(esgf_dir, credentials_file=None, certificates_tarball=None):
    if credentials_file:
        shutil.copy(op.join(TEST_DATA_DIR, credentials_file),
                    op.join(esgf_dir, 'credentials.pem'))
    if certificates_tarball:
        os.system('cd %s ; tar zxf %s' %
                  (esgf_dir, op.join(TEST_DATA_DIR,
                                     certificates_tarball)))


def _clear_creds(esgf_dir):
    cred_path = op.join(esgf_dir, ESGF_CREDENTIALS)
    if op.exists(cred_path):
        os.remove(cred_path)


def _clear_certs(esgf_dir):
    cert_path = op.join(esgf_dir, 'certificates')
    if op.exists(cert_path):
        shutil.rmtree(cert_path)


@pytest.mark.skipif(not _has_login_info,
                    reason='Must have specified login info as environment variables.')
class TestLogon(TestCase):
    def setUp(self):
        self.esgf_dir = tempfile.mkdtemp(prefix='pyesgf_tmp')

    def tearDown(self):
        if op.exists(self.esgf_dir):
            shutil.rmtree(self.esgf_dir)

    @pytest.mark.skipif(not _has_myproxy, reason='Cannot work.')
    def test_no_logon(self):
        _clear_creds(self.esgf_dir)
        lm = LogonManager(self.esgf_dir)
        assert not lm.is_logged_on()

    @pytest.mark.skipif(not _has_myproxy, reason='Cannot work.')
    def test_expired(self):
        _load_creds(self.esgf_dir, credentials_file='expired.pem')
        lm = LogonManager(self.esgf_dir)
        assert lm.state == lm.STATE_EXPIRED_CREDENTIALS

    @pytest.mark.skipif(not _has_myproxy, reason='Cannot work.')
    def test_logon(self, extra_args=None):
        _clear_creds(self.esgf_dir)
        _load_creds(self.esgf_dir, certificates_tarball='pcmdi9-certs.tar.gz')

        if not extra_args: extra_args = {}
        lm = LogonManager(self.esgf_dir, **extra_args)
        lm.logon(TEST_USER, TEST_PASSWORD, TEST_MYPROXY)

        assert lm.is_logged_on()

    @pytest.mark.skipif(not _has_myproxy, reason='Cannot work.')
    def test_logon_with_verify_true(self):
        self.test_logon({'verify': True})

    @pytest.mark.skipif(not _has_myproxy, reason='Cannot work.')
    def test_logon_with_verify_false(self):
        self.test_logon({'verify': False})

    @pytest.mark.skipif(not _has_myproxy, reason='Cannot work.')
    def test_bootstrap(self):
        _clear_creds(self.esgf_dir)
        lm = LogonManager(self.esgf_dir)
        lm.logon(TEST_USER, TEST_PASSWORD, TEST_MYPROXY, bootstrap=True)

        assert lm.is_logged_on()

    @pytest.mark.skipif(not _has_myproxy, reason='Cannot work.')
    def test_logoff(self):
        lm = LogonManager(self.esgf_dir)

        # Only re-logon if credentials are not valid
        if not lm.is_logged_on():
            lm.logon(TEST_USER, TEST_PASSWORD, TEST_MYPROXY, bootstrap=True)

        assert lm.is_logged_on()
        lm.logoff()

        assert not op.exists(op.join(self.esgf_dir, 'credentials.pem'))
        assert not lm.is_logged_on()
        assert lm.state == lm.STATE_NO_CREDENTIALS

    # NOTE: This line should replace the xfail if bug is fixed
    # @pytest.mark.skipif(not _has_myproxy, reason='Cannot work.')
    @pytest.mark.xfail(reason=('Obtaining username from '
                               'openid is not working.'))
    def test_logon_openid(self):
        _clear_creds(self.esgf_dir)
        _load_creds(self.esgf_dir, certificates_tarball='pcmdi9-certs.tar.gz')
        lm = LogonManager(self.esgf_dir)

        # NOTE: for many users the OpenID lookup might not provide the username
        #       in which case this test will fail because it needs interactive
        #       prompting for a username.
        lm.logon_with_openid(TEST_OPENID, TEST_PASSWORD, interactive=False)

        assert lm.is_logged_on()
