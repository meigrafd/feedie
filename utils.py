import ssl
import string
import UserDict
import htmlentitydefs
import sgmllib
import urllib2
from time import sleep
from urllib import urlencode


class URLShortener(object):
    def __init__(self, service):
        self.services = {
            'v.gd':         'https://v.gd/create.php?format=simple&',
            'tinyurl.com':  'http://tinyurl.com/api-create.php?',
        }
        self.headers = {
            'User-Agent': "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.2.2) Gecko/20100316 Firefox/3.6.2",
        }
        self.service_url = self.services[service]
        #self.sslContext = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        #self.sslContext = ssl.create_default_context()
    
    
    def shorten_url(self, long_url):
        response_body = None
        data = urlencode({'url': long_url})
        request_url = "{0}{1}".format(self.service_url, data)
        request = urllib2.Request(request_url, data=data, headers=self.headers)
        #opener = urllib2.build_opener(urllib2.HTTPSHandler(context=self.sslContext))
        try:
            #connection = opener.open(request)
            #connection = urllib2.urlopen(request, context=self.sslContext)
            connection = urllib2.urlopen(request)
            response_headers = connection.headers
            response_body = connection.read()
        except urllib2.HTTPError as error:
            print('%s:%s' % (error.code, error.msg))
            #sleep(2)
            #response_body = self.shorten_url(long_url)

        try: connection.close()
        except: pass
        return response_body
    


class InsensitivePreservingDict(UserDict.DictMixin, object):
    def key(self, s):
        """Override this if you wish."""
        if s is not None:
            s = s.lower()
        return s

    def __init__(self, dict=None, key=None):
        if key is not None:
            self.key = key
        self.data = {}
        if dict is not None:
            self.update(dict)

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, super(InsensitivePreservingDict, self).__repr__())

    def fromkeys(cls, keys, s=None, dict=None, key=None):
        d = cls(dict=dict, key=key)
        for key in keys:
            d[key] = s
        return d
    fromkeys = classmethod(fromkeys)

    def __getitem__(self, k):
        return self.data[self.key(k)][1]

    def __setitem__(self, k, v):
        self.data[self.key(k)] = (k, v)

    def __delitem__(self, k):
        del self.data[self.key(k)]

    def iteritems(self):
        return self.data.itervalues()

    def keys(self):
        L = []
        for (k, _) in self.iteritems():
            L.append(k)
        return L

    def __reduce__(self):
        return (self.__class__, (dict(self.data.values()),))

class IrcDict(InsensitivePreservingDict):
    """Subclass of dict to make key comparison IRC-case insensitive."""
    def key(self, s):
        if s is not None:
            s = toLower(s)
        return s

_rfc1459trans = string.maketrans(string.ascii_uppercase + r'\[]~', string.ascii_lowercase + r'|{}^')
def toLower(s, casemapping=None):
    """s => s
    Returns the string s lowered according to IRC case rules."""
    if casemapping is None or casemapping == 'rfc1459':
        return s.translate(_rfc1459trans)
    elif casemapping == 'ascii': # freenode
        return s.lower()
    else:
        raise ValueError, 'Invalid casemapping: %r' % casemapping

def normalizeWhitespace(s):
    """Normalizes the whitespace in a string; \s+ becomes one space."""
    return ' '.join(s.split())

class HtmlToText(sgmllib.SGMLParser):
    """Taken from some eff-bot code on c.l.p."""
    entitydefs = htmlentitydefs.entitydefs.copy()
    entitydefs['nbsp'] = ' '
    def __init__(self, tagReplace=' '):
        self.data = []
        self.tagReplace = tagReplace
        sgmllib.SGMLParser.__init__(self)

    def unknown_starttag(self, tag, attr):
        self.data.append(self.tagReplace)

    def unknown_endtag(self, tag):
        self.data.append(self.tagReplace)

    def handle_data(self, data):
        self.data.append(data)

    def getText(self):
        text = ''.join(self.data).strip()
        return normalizeWhitespace(text)

def htmlToText(s, tagReplace=' '):
    """Turns HTML into text.  tagReplace is a string to replace HTML tags with.
    """
    x = HtmlToText(tagReplace)
    x.feed(s)
    return x.getText()


