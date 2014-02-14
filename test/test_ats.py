"""
Test Attribute Service API.

"""

from pyesgf.security.ats import AttributeService

CEDA_ATS = 'https://esgf-index1.ceda.ac.uk/esgf-idp/saml/soap/secure/attributeService.htm'

def test_ceda_ats():
    service = AttributeService(CEDA_ATS)
    openid = 'https://ceda.ac.uk/openid/Stephen.Pascoe'
    resp = service.send_request(openid, ['urn:esg:first:name', 'urn:esg:last:name'])

    assert resp.get_subject() == openid
    
    attrs = resp.get_attributes()
    assert attrs['urn:esg:first:name'] == 'Stephen'
    assert attrs['urn:esg:last:name'] == 'Pascoe'
    
