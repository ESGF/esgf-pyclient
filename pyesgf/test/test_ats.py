"""
Test Attribute Service API.

"""

from pyesgf.security.ats import AttributeService
from pyesgf.node import ESGFNode
import pytest
from unittest import TestCase

CEDA_NODE = ESGFNode('https://esgf-index1.ceda.ac.uk')
OPENID = 'https://ceda.ac.uk/openid/Ag.Stephens'


class TestATS(TestCase):
    @pytest.mark.xfail(reason='This test does not work anymore.')
    def test_ceda_ats(self):
        service = AttributeService(CEDA_NODE.ats_url, 'esgf-pyclient')
        fn, ln = 'Ag', 'Stephens'
        resp = service.send_request(OPENID, ['urn:esg:first:name',
                                             'urn:esg:last:name'])

        assert resp.get_subject() == OPENID

        attrs = resp.get_attributes()
        assert attrs['urn:esg:first:name'] == fn
        assert attrs['urn:esg:last:name'] == ln

    def test_unknown_principal(self):
        service = AttributeService(CEDA_NODE.ats_url, 'esgf-pyclient')
        openid = 'https://example.com/unknown'

        resp = service.send_request(openid, [])

        assert resp.get_status() == ('urn:oasis:names:tc:SAML:2.0:'
                                     'status:UnknownPrincipal')

    @pytest.mark.xfail(reason='This test does not work anymore.')
    def test_multi_attribute(self):
        service = AttributeService(CEDA_NODE.ats_url, 'esgf-pyclient')

        resp = service.send_request(OPENID, ['CMIP5 Research'])

        attrs = resp.get_attributes()
        assert list(sorted(attrs['CMIP5 Research'])) == ['default', 'user']
