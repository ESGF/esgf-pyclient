"""
A Cache for HTTP requests for use when unittesting.

Courtesy of Staffan Malmgren <staffan@tomtebo.org> http://code.activestate.com/recipes/491261/
Some simplifications applied.

"""


import urllib2
import httplib
import os
import StringIO
import md5

def install_cache(cache_dir):
    h = CacheHandler(cache_dir)
    opener = urllib2.build_opener(h)
    urllib2.install_opener(opener)


class CacheHandler(urllib2.BaseHandler):
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


class CachedResponse(StringIO.StringIO):
    """An urllib2.response-like object for cached responses.

    To determine wheter a response is cached or coming directly from
    the network, check the x-cache header rather than the object type."""
    
    def ExistsInCache(cacheLocation, url):
        hash = md5.new(url).hexdigest()
        return (os.path.exists(cacheLocation + "/" + hash + ".headers") and 
                os.path.exists(cacheLocation + "/" + hash + ".body"))
    ExistsInCache = staticmethod(ExistsInCache)

    def StoreInCache(cacheLocation, url, response):
        hash = md5.new(url).hexdigest()
        f = open(cacheLocation + "/" + hash + ".headers", "w")
        headers = str(response.info())
        f.write(headers)
        f.close()
        f = open(cacheLocation + "/" + hash + ".body", "w")
        f.write(response.read())
        f.close()
    StoreInCache = staticmethod(StoreInCache)
    
    def __init__(self, cacheLocation,url,setCacheHeader=True):
        self.cacheLocation = cacheLocation
        hash = md5.new(url).hexdigest()
        StringIO.StringIO.__init__(self, file(self.cacheLocation + "/" + hash+".body").read())
        self.url     = url
        self.code    = 200
        self.msg     = "OK"
        headerbuf = file(self.cacheLocation + "/" + hash+".headers").read()
        if setCacheHeader:
            headerbuf += "x-cache: %s/%s\r\n" % (self.cacheLocation,hash)
        self.headers = httplib.HTTPMessage(StringIO.StringIO(headerbuf))

    def info(self):
        return self.headers
    def geturl(self):
        return self.url
