"""
Test Attribute Service API.

"""

import os

from pyesgf.security.ats import AttributeService
from pyesgf.node import ESGFNode
import pytest
from unittest import TestCase

ESGF_NODE = ESGFNode('https://esgf-node.llnl.gov')
TEST_OPENID = os.environ.get('LLNL_OPENID')
TEST_USER_DETAILS = os.environ.get('LLNL_NAME').split()


class TestATS(TestCase):
#    @pytest.mark.xfail(reason='This test does not work anymore.')
    def test_ceda_ats(self):
        service = AttributeService(ESGF_NODE.ats_url, 'esgf-pyclient')
        fn, ln = TEST_USER_DETAILS
        resp = service.send_request(TEST_OPENID, ['urn:esg:first:name',
                                             'urn:esg:last:name'])

        assert resp.get_subject() == TEST_OPENID

        attrs = resp.get_attributes()
        assert attrs['urn:esg:first:name'] == fn
        assert attrs['urn:esg:last:name'] == ln

    def test_unknown_principal(self):
        service = AttributeService(ESGF_NODE.ats_url, 'esgf-pyclient')
        openid = 'https://example.com/unknown'

        resp = service.send_request(openid, [])

        assert resp.get_status() == ('urn:oasis:names:tc:SAML:2.0:'
                                     'status:UnknownPrincipal')

#    @pytest.mark.xfail(reason='This test does not work anymore.')
    def test_multi_attribute(self):
        service = AttributeService(ESGF_NODE.ats_url, 'esgf-pyclient')
        CMIP5_RESEARCH = 'CMIP5 Research'

        resp = service.send_request(TEST_OPENID, [CMIP5_RESEARCH])

        attrs = resp.get_attributes()
        assert attrs[CMIP5_RESEARCH] == 'user'
