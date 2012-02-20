__doc__ = """
This is a very simple and naive implementation of a tree of resources.
The api is designed work fine with backbone.js
It seems a dictionary with a few key differences: 
 - the keys are strings (they maps itself on urls)
 - the values are a file object
 - You must request a new key before assign a value
 - every resource has an etag and mimetype
"""

import os
import os.path
from hashlib import md5
import mimetypes
from forrest.app import RestApp
from StringIO import StringIO
import json

class FileSystem(object):
    def __init__(self, **config):
        self.root = config['path'].replace('/',os.path.sep)
        self.index_html = config.get('index_html')
        self.etags = {}
        # prebuild the dict
        for root, dirs, files in os.walk(self.root):
            for name in files:
                if (not name.startswith('.')):
                    fullpath = os.path.join(root, name)
                    with open(fullpath,'rb') as f: 
                        self.etags[fullpath] = md5(f.read()).hexdigest()

    def _getFilename(self, fn):
        fn = fn.replace('/',os.path.sep)
        if not fn and self.index_html:
            return os.path.join(self.root, self.index_html)
        return os.path.join(self.root, fn.lstrip(os.path.sep))

    def _title2id(self, title, mime):
        if not title:
            title = u'item'
        if not isinstance(title, unicode):
            title = unicode(title, 'utf-8')
        s = title.encode('ascii', 'ignore')
        s = s.translate(None,'''!"#$%&\'()*+,/:;<=>?@[\\]^`{|}~''')
        extension = self._guessExtension(mime) or ""
        return "-".join(s.split()) + extension

    def get(self, key, options=None):
        filename = self._getFilename(key)
        try:
            return open(filename, 'rb'), os.path.getsize(filename)
        except IOError, OSError:
            pass
        data = []
        try:
            ls = sorted(os.listdir(filename))
        except:
            raise KeyError, 'not found'
        for fname in ls: # throw OSError
            fullpath = os.path.join(filename,fname)
            if not os.path.isfile(fullpath) or fname.startswith('.'):
                continue
            mimetype = self._getMimeType(fullpath)
            if "json" in mimetype:
                try:
                    with open(fullpath) as f:
                        data.append(f.read())
                except IOError:
                    continue # I can't open (maybe is removed)
            else:
                data.append('{"id":"%s","mimetype":"%s"}' % (fname,mimetype) )
        content = '[' + ','.join(data) + ']'
        return StringIO(content), len(content)

    def set(self, key, stream, length, mime):
        filename = self._getFilename(key)
        if filename not in self.etags:
            raise KeyError, "key not found"

#        if mime != self._getMimeType(filename):
#            raise KeyError, 'Resource mime changes are not admitted'

        try:
            value = 'json' in mime.lower() and self._insertId(stream.read(length), os.path.basename(key)) or stream.read(length)
            with open(filename, 'wb') as f: # throw IOError
                f.write(value)
            self.etags[filename] = md5(value).hexdigest()
        except IOError:
            raise KeyError, 'File not found'
        except ValueError:
            raise KeyError, 'not a valid JSON'
        
    def _insertId(self, value, key):
        obj = json.loads(value)
        obj['id'] = key
        return json.dumps(obj)

    def delete(self, key):
        filename = self._getFilename(key)
        try:
            os.remove(filename)
            del self.etags[filename]
        except OSError:
            raise KeyError, 'not found'
         

    def new(self, parent, title, mime):
        dirname = self._getFilename(parent)
        if not os.path.isdir(dirname):
            raise KeyError, '%s: not a dir.' % dirname

        newid = self._title2id(title, mime)

        n = 1
        path = os.path.join(dirname, newid)
        p,e = os.path.splitext(path)
        while path in self.etags:
            path = ''.join([p, str(n), e])
            n +=1
        self.etags[path] = None
        newid = os.path.basename(path)
        return newid

    def _getMimeType(self, filename):
        if filename.lower().endswith('.json'):
            return 'application/json'
        return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

    def _guessExtension(self, mime):
        """windows doesn't know application/json (sad face)"""
        if 'json' in mime:
            return '.json'
        return mimetypes.guess_extension(mime) or ""


    def mime(self, key):
        filename = self._getFilename(key)
        if os.path.isdir(filename):
            return 'application/json'
        if os.path.isfile(filename):
            return self._getMimeType(filename)
        raise KeyError

    def etag(self, key):
        filename = self._getFilename(key)
        if os.path.isdir(filename):
            return None
        return self.etags[filename]



