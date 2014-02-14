"""
Interface to the ESGF SAML Attribute Service.

"""

from jinja2 import Template
import uuid
import datetime
import urllib2
from xml.etree import ElementTree as ET

ATS_REQUEST_TMPL = Template('''<?xml version="1.0" encoding="UTF-8"?>
<soap11:Envelope xmlns:soap11="http://schemas.xmlsoap.org/soap/envelope/">
  <soap11:Body>
     <samlp:AttributeQuery xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol" 
                           ID="{{ msg_id }}" 
                           IssueInstant="{{timestamp}}" Version="2.0">
        <saml:Issuer xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion" Format="urn:oasis:names:tc:SAML:1.1:nameid-format:X509SubjectName">{{ issuer }}</saml:Issuer>
        <saml:Subject xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion">
           <saml:NameID Format="urn:esg:openid">{{ openid }}</saml:NameID>
        </saml:Subject>
        {% for attr in attributes -%}
        <saml:Attribute xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
                        FriendlyName="{{ attr.name }}"
                        Name="{{ attr.urn }}"
                        NameFormat="{{ attr.format }}"/>
        {% endfor -%}
     </samlp:AttributeQuery>
  </soap11:Body>
</soap11:Envelope>
''')


NS = {
    'soap11': "http://schemas.xmlsoap.org/soap/envelope/",
    'saml2p': "urn:oasis:names:tc:SAML:2.0:protocol",
    'saml': "urn:oasis:names:tc:SAML:2.0:assertion",
}


class SAMLAttribute(object):
    def __init__(self, fname, urn, format=None):
        self.fname = fname
        self.urn = urn
        if format:
            self.format = format
        else:
            self.format = 'http://www.w3.org/2001/XMLSchema#string'

class SAMLAttributeStore(dict):
    def add(self, attribute):
        self[attribute.urn] = attribute

    def get_by_friendly_name(self, friendly_name):
        for attr in self.values():
            if attr.fname == friendly_name:
                return attr
        else:
            raise KeyError('No SAML attribute matches name %s' % repr(friendly_name))
        

SAML_ATTRS = SAMLAttributeStore()
SAML_ATTRS.add(SAMLAttribute('FirstName', 'urn:esg:first:name'))
SAML_ATTRS.add(SAMLAttribute('LastName', 'urn:esg:last:name'))
SAML_ATTRS.add(SAMLAttribute('EmailAddress', 'urn:esg:email:address'))
SAML_ATTRS.add(SAMLAttribute('GroupRole', 'urn:esg:group:role', 'groupRole'))

class AttributeService(object):
    ISSUER = 'ats_tool'
    def __init__(self, url):
        self.url = url

    def build_request(self, openid, attributes):
        now = datetime.datetime.utcnow()

        # Map attribute urns to classes
        attrs = [SAML_ATTRS[a] for a in attributes]

        return ATS_REQUEST_TMPL.render(
            msg_id=uuid.uuid1(),
            timestamp=now.isoformat()+'Z',
            issuer=self.ISSUER,
            openid=openid,
            attributes=attrs)

    def send_request(self, openid, attributes):
        post_body = self.build_request(openid, attributes)
        req = urllib2.Request(self.url, post_body)
        req.add_header('Content-Type', 'text/xml')
        req.add_header('Content-Length', str(len(req.get_data())))
        print req.headers
        print req.get_data()
        resp = urllib2.urlopen(req)

        return AttributeServiceResponse(resp)


class AttributeServiceResponse(object):
    def __init__(self, source):
        self.xml = ET.parse(source)

    def get_subject(self):
        fpath = './/{{{0}}}Subject/{{{0}}}NameID'.format(NS['saml'])
        subject_el = self.xml.find(fpath)

        return subject_el.text

    def get_attributes(self):
        d = {}
        fpath = './/{{{0}}}AttributeStatement/{{{0}}}Attribute'.format(NS['saml'])
        for el in self.xml.findall(fpath):
            attr_name = el.get('Name')
            val_el = el.find('./{{{0}}}AttributeValue'.format(NS['saml']))
            attr_value = val_el.text

            d[attr_name] = attr_value

        return d

