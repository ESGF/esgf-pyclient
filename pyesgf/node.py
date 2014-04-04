"""
Convenience interface for defining service URL endpoints for ESGF nodes

"""

class ESGFNode(object):
    def __init__(self, base_url):
        # Strip '/' from url as necessary
        self.base_url = base_url.rstrip('/')

    @property
    def search_url(self):
        """
        Return the URL of the esg-search service.

        This URL is the prefix required for search and wget endpoints.
        """
        return '/'.join(self.base_url, 'esg-search')

    @property
    def ats_url(self):
        """
        Return the URL for the ESGF SAML AttributeService
        """
        return '/'.join([self.base_url,
                        'esgf-idp/saml/soap/secure/attributeService.htm'])

    @property
    def azs_url(self):
        """
        Return the URL for the ESGF SAML AuthorizationService.
        """
        return '/'.join([self.base_url,
                        'esgf-orp/saml/soap/secure/authorizationService.htm'])

    
        
