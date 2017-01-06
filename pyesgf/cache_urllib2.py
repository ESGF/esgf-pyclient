"""
A Cache for HTTP requests for use when unittesting.

Courtesy of Staffan Malmgren <staffan@tomtebo.org> http://code.activestate.com/recipes/491261/
Some simplifications applied.

"""


from six.moves.urllib.request import build_opener, install_opener, BaseHandler
from six.moves.http_client import HTTPMessage
from six import StringIO
import os
from hashlib import md5

def install_cache(cache_dir):
    h = CacheHandler(cache_dir)
    opener = build_opener(h)
    install_opener(opener)

def remove_from_cache(url, cache_dir):
    hash = _md5_url(url)
    prefix = os.path.join(cache_dir, hash)
    if os.path.exists(prefix+'.headers'):
        os.remove(prefix+'.headers')
        os.remove(prefix+'.body')
    else:
        raise RuntimeError('No cache found for %s' % hash)

class CacheHandler(BaseHandler):
    """Stores responses in a persistant on-disk cache.

    If a subsequent GET request is made for the same URL, the stored
    response is returned, saving time, resources and bandwith"""
    def __init__(self,cacheLocation):
        """The location of the cache directory"""
        self.cacheLocation = cacheLocation
        if not os.path.exists(self.cacheLocation):
            os.mkdir(self.cacheLocation)

    def default_open(self,request):
        if ((request.get_method() == "GET") and 
            (CachedResponse.ExistsInCache(self.cacheLocation, request.get_full_url()))):
            return CachedResponse(self.cacheLocation, request.get_full_url(), setCacheHeader=True)	
        else:
            return None # let the next handler try to handle the request

    def http_response(self, request, response):
        if request.get_method() == "GET":
            CachedResponse.StoreInCache(self.cacheLocation, request.get_full_url(), response)
            return CachedResponse(self.cacheLocation, request.get_full_url(), setCacheHeader=False)
        else:
            return response


def _md5_url(url):
    if hasattr(url, 'encode'):
        hash = md5(url.encode('utf-8')).hexdigest()
    else:
        hash = md5(url).hexdigest()
    return hash


class CachedResponse(StringIO):
    """An urllib2.response-like object for cached responses.

    To determine wheter a response is cached or coming directly from
    the network, check the x-cache header rather than the object type."""
    
    def ExistsInCache(cacheLocation, url):
        hash = _md5_url(url)
        return (os.path.exists(cacheLocation + "/" + hash + ".headers") and 
                os.path.exists(cacheLocation + "/" + hash + ".body"))
    ExistsInCache = staticmethod(ExistsInCache)

    def StoreInCache(cacheLocation, url, response):
        hash = _md5_url(url)
        f = open(cacheLocation + "/" + hash + ".headers", "w")
        headers = str(response.info())
        f.write(headers)
        f.close()
        f = open(cacheLocation + "/" + hash + ".body", "wb")
        f.write(response.read())
        f.close()
    StoreInCache = staticmethod(StoreInCache)
    
    def __init__(self, cacheLocation,url,setCacheHeader=True):
        self.cacheLocation = cacheLocation
        hash = _md5_url(url)
        StringIO.__init__(self, open(self.cacheLocation + "/" + hash + ".body", 'r').read())
        self.url     = url
        self.code    = 200
        self.msg     = "OK"
        headerbuf = open(self.cacheLocation + "/" + hash + ".headers", 'r').read()
        if setCacheHeader:
            headerbuf += "x-cache: %s/%s\r\n" % (self.cacheLocation,hash)
        self.headers = HTTPMessage(StringIO(headerbuf))

    def info(self):
        return self.headers
    def geturl(self):
        return self.url
