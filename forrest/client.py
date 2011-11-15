import httplib2
from urllib import quote
from urlparse import urljoin

from model import GenericResourceModel

class RemoteResourceModel(GenericResourceModel):

    def __init__(self,url):
        self.url = url
        self.http = httplib2.Http(".cache")

    def query(self,**args):
        if args:
            query_string = '?' + quote('&'.join(["%s=%s" for k,v in args.iteritems()]))
        else:
            query_string = ''
        (resp_headers, content) = http.request(urljoin(self.url, query_string), "GET")
        input_format = resp_headers['CONTENT_TYPE']
        return content, input_format
                
    def get(self,key):
        (resp_headers, content) = http.request(urljoin(self.url, key), "GET")
        input_format = resp_headers['CONTENT_TYPE']
        return content, input_format

    def put(self,key,data,mime_type = None):
        headers['content-type'] = mime_type
        (resp, content) = h.request(urljoin(self.url, key), 
                                    "PUT", body=data, 
                                    headers=headers )
        


    def new(self,data,mime_type = None, title = None):
        headers['content-type'] = mime_type
        (resp, content) = h.request(self.url, 
                                    "POST", body=data, 
                                    headers=headers )

        if resp_headers['Location'].startswith(self.url):
            return resp_headers['Location'][len(self.url):]
        return resp_headers['Location']
        

    def delete(self,key):
        (resp, content) = h.request(urljoin(self.url, key), 
                                    "DELETE", body="", 
                                    headers={} )
                                    
                                    
import httplib2
from urlparse import urljoin
import mimetypes
import json

http = httplib2.Http(".cache")
#http.add_credentials('name', 'password')        

class Resource(object):
    """either an object or a file"""
    def __init__(self, urlRoot, key = None):
        self.urlRoot = urlRoot
        self.key = key
        self.content = None
        self.mimetype = 'application/json'

    def isNew(self):
        return self.key is None

    def fetch(self):
        if key:
            raise KeyError
        (resp_headers, content) = http.request(urljoin(self.urlRoot, key), "GET")
        if resp_headers.status == '200':
            self.mimetype = resp_headers['CONTENT_TYPE']
            self.content = 'json' in self.mimetype or json.loads(content) and content
        raise KeyError
                
    def save(self):
        data = 'json' in self.mimetype and json.dumps(self.content) or self.content
        headers = []
        if not key: #issue a POST request
            (resp, content) = http.request(self.urlRoot, "POST",
                                           body=data, 
                                           headers=headers )
        else: # or a PUT request
            (resp, content) = http.request(urljoin(self.urlRoot, key), "PUT",
                                           body=data, 
                                           headers=headers )
        
    def get(self):
        return self.content

    def set(self, content, filename=''):
        self.mimetype = mimetypes.guess_type(filename)[0] or 'application/json'
        self.content = content
    
    def __delete__(self):
        
        
class Collection(object):
        
