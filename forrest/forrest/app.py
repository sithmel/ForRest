from urllib import quote, unquote_plus
from contextlib import closing

###############################################
# Utilities
###############################################
BLOCK_SIZE = 8192

def send_file(f):
    with closing(f):
        block = f.read(BLOCK_SIZE)
        while block:
            yield block
            block = f.read(BLOCK_SIZE)
            
def get_base_url(environ):
    url = environ['wsgi.url_scheme']+'://'

    if environ.get('HTTP_HOST'):
        url += environ['HTTP_HOST']
    else:
        url += environ['SERVER_NAME']

        if environ['wsgi.url_scheme'] == 'https':
            if environ['SERVER_PORT'] != '443':
               url += ':' + environ['SERVER_PORT']
        else:
            if environ['SERVER_PORT'] != '80':
               url += ':' + environ['SERVER_PORT']

    url += quote(environ.get('SCRIPT_NAME',''))
    return url
        
def get_args(data):
    data = data.strip()
    ret = {}
    for val in data.split('&'):
        val = val.split('=', 1)
        if not val[0]: continue
        k = val[0].lower()
        if len(val) > 1: v = val[1]
        else: v = ''
        ret[k] = unquote_plus(v)
    return ret
    
#def get_input(stream,length):
#    """get input data and return data as it is"""
#    data = stream.read(length)
#    return data


#
# wsgi functions
#
def not_found(environ, start_response):
    """Called if no URL matches."""
    start_response('404 NOT FOUND', [('Content-Type', 'text/plain'), ('Content-Length','9')])
    return ['Not Found']

def not_modified(environ, start_response):
    """Called if etag match"""
    start_response('304 Not Modified', [('Content-Type', 'text/plain'), ('Content-Length','12')])
    return ['Not Modified']

def precondition_failed(environ, start_response):
    """Called if etag doesn't match in put requests"""
    start_response('412 Precondition Failed', [('Content-Type', 'text/plain'), ('Content-Length','19')])
    return ['Precondition Failed']

class RestApp(object):
    def __init__(self, conf):
        self.resources = conf['resources']

    def __call__(self, environ, start_response):
        method = environ.get("X-HTTP-METHOD-OVERRIDE")
        if not method:
            method = environ["REQUEST_METHOD"]
        return getattr(self,'method_%s' % method.lower())(environ, start_response)

    def method_get(self, environ, start_response):
        input_etag = environ.get('HTTP_IF_NONE_MATCH')
        name = environ['PATH_INFO'].strip('/')

        try:
            etag = self.resources.etag(name)
        except KeyError:
            etag = None
            
        if input_etag and etag and input_etag == etag:
            return not_modified(environ, start_response)

        try:
            contentstream, contentlength = self.resources.get(name)
        except KeyError:
            return not_found(environ, start_response)

        status = '200 OK'
        headers = [('Content-Type', self.resources.mime(name)),
                   ('Content-Length', str(contentlength))]
        
        if etag:
            headers.append(('ETag',etag))

        start_response(status, headers)
        return send_file(contentstream)

    def method_delete(self, environ, start_response):
        name = environ['PATH_INFO'].strip('/')

        input_etag = environ.get('HTTP_IF_MATCH')

        try:
            etag = self.resources.etag(name)
        except KeyError:
            etag = None

        if input_etag and input_etag != '*' and etag and input_etag != etag:
            return precondition_failed(environ, start_response)

        try:
            self.resources.delete(name)
        except KeyError:
            return not_found(environ, start_response)
        status = '200 OK'
        content = '{"status":"ok"}'
        headers = [('Content-Type','application/json'),
                   ('Content-Length',str(len(content)))]

        start_response(status, headers)
        return [content]

    def method_put(self, environ, start_response):
        name = environ['PATH_INFO'].strip('/')
        input_etag = environ.get('HTTP_IF_MATCH')
        content_type = environ.get('CONTENT_TYPE','application/octet-stream').split(';',1)[0]

        try:
            etag = self.resources.etag(name)
        except KeyError:
            etag = None

        if input_etag and input_etag != '*' and etag and input_etag != etag:
            return precondition_failed(environ, start_response)

        try:
            self.resources.set(name, environ['wsgi.input'],int(environ.get('CONTENT_LENGTH','0')), content_type)
        except KeyError:
            return not_found(environ, start_response)


        if content_type == "application/json":
            contentstream, contentlength = self.resources.get(name)
            content = send_file(contentstream)
        else:
            content = ['{}']
            contentlength = len(content[0])

        headers = [('Content-Type','application/json'),
                   ('Content-Length',str(contentlength))]
        status = '200 OK'
        start_response(status, headers)
        return content

    def method_post(self, environ, start_response):
        name = environ['PATH_INFO'].strip('/')
        content_type = environ.get('CONTENT_TYPE','application/octet-stream').split(';',1)[0]

        proposed_title = environ.get('SLUG',None)

        try:
            newid = self.resources.new(name, proposed_title, content_type)
            newpath = name + '/' + newid
            self.resources.set(newpath.lstrip('/'), environ['wsgi.input'],int(environ.get('CONTENT_LENGTH','0')), content_type)
        except KeyError:
            return not_found(environ, start_response)

        status = '201 Created'
        if content_type == "application/json":
            contentstream, contentlength = self.resources.get(newpath)
            content = send_file(contentstream)
        else:
            content = ['{"id":"%s"}' % newid, ]
            contentlength = len(content[0])
        headers = [('Location',newid),
                   ('Content-Type','application/json'),
                   ('Content-Length',str(contentlength))]

        start_response(status, headers)
        return content

            
