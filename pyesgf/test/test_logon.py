"""
tests for pyesgf.logon module.

"""

import tempfile
import os
import os.path as op
import shutil

from pyesgf.logon import LogonManager, ESGF_CREDENTIALS
import pytest
try:
    from myproxy.client import MyProxyClient
    import OpenSSL
    _has_myproxy = True
except ImportError:
    _has_myproxy = False

TEST_USER = os.environ.get('USERNAME')
TEST_PASSWORD = os.environ.get('PASSWORD')
TEST_OPENID = os.environ.get('OPENID')
TEST_MYPROXY = 'slcs1.ceda.ac.uk'

esgf_dir = None
test_data_dir = op.join(op.dirname(__file__), 'data')


def setup_module():
    global esgf_dir
    esgf_dir = tempfile.mkdtemp(prefix='pyesgf_tmp')


def teardown_module():
    if op.exists(esgf_dir):
        shutil.rmtree(esgf_dir)


def _load_creds(credentials_file=None, certificates_tarball=None):
    if credentials_file:
        shutil.copy(op.join(test_data_dir, credentials_file),
        op.join(esgf_dir, 'credentials.pem'))
    if certificates_tarball:
        os.system('cd %s ; tar zxf %s' %
                  (esgf_dir, op.join(test_data_dir,
                                     certificates_tarball)))


def _clear_creds():
    cred_path = op.join(esgf_dir, ESGF_CREDENTIALS)
    if op.exists(cred_path):
        os.remove(cred_path)


def _clear_certs():
    cert_path = op.join(esgf_dir, 'certificates')
    if op.exists(cert_path):
        shutil.rmtree(cert_path)


def test_no_logon():
    _clear_creds()
    lm = LogonManager(esgf_dir)
    assert lm.is_logged_on() == False


def test_expired():
    _load_creds('expired.pem')
    lm = LogonManager(esgf_dir)
    assert lm.state == lm.STATE_EXPIRED_CREDENTIALS


@pytest.mark.skipif(not _has_myproxy, reason='Cannot work.')
def test_logon():
    _clear_creds()
    _load_creds(certificates_tarball='pcmdi9-certs.tar.gz')
    lm = LogonManager(esgf_dir)
    lm.logon(TEST_USER, TEST_PASSWORD, TEST_MYPROXY)

    assert lm.is_logged_on()


@pytest.mark.skipif(not _has_myproxy, reason='Cannot work.')
def test_bootstrap():
    _clear_creds()
    lm = LogonManager(esgf_dir)
    lm.logon(TEST_USER, TEST_PASSWORD, TEST_MYPROXY, bootstrap=True)

    assert lm.is_logged_on()


@pytest.mark.skipif(not _has_myproxy, reason='Cannot work.')
def test_logoff():
    lm = LogonManager(esgf_dir)

    # Only re-logon if credentials are not valid
    if not lm.is_logged_on():
        lm.logon(TEST_USER, TEST_PASSWORD, TEST_MYPROXY, bootstrap=True)

    assert lm.is_logged_on()
    lm.logoff()

    assert not op.exists(op.join(esgf_dir, 'credentials.pem'))
    assert not lm.is_logged_on()
    assert lm.state == lm.STATE_NO_CREDENTIALS


# NOTE: This line should replace the xfail if bug is fixed
# @pytest.mark.skipif(not _has_myproxy, reason='Cannot work.')
@pytest.mark.xfail(reason='Obtaining username from ''openid is not working.')
def test_logon_openid():
    _clear_creds()
    _load_creds(certificates_tarball='pcmdi9-certs.tar.gz')
    lm = LogonManager(esgf_dir)

    # NOTE: for many users the OpenID lookup might not provide the username
    #       in which case this test will fail because it needs interactive
    #       prompting for a username.
    lm.logon_with_openid(TEST_OPENID, TEST_PASSWORD, interactive=False)

    assert lm.is_logged_on()
