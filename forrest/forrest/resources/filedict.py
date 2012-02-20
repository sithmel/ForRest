import shelve
from hashlib import md5
import mimetypes
import os.path
import threading
from StringIO import StringIO
import json

class FileDict(object):
    def __init__(self, **config):
        self.root = config['path']
        self.data = shelve.open(self.root)
        self.lock = threading.Lock()


    def _title2id(self, title, mime):
        if not title:
            title = 'item'
        if not isinstance(title, unicode):
            title = unicode(title, 'utf-8')
        s = title.encode('ascii', 'ignore')
        s = s.translate(None,'''!"#$%&\'()*+,/:;<=>?@[\\]^`{|}~''')
        extension = mimetypes.guess_extension(mime) or ""
        return "-".join(s.split()) + extension

    def get(self, key, options=None):
        value = self.data[key]
        return StringIO(value), len(value)
            
    def set(self, key, stream, length, mime):
        if key not in self.data:
            raise KeyError, "key not found"

        if mime != self.mime(key):
            raise KeyError, 'Resource mime changes are not admitted'

        try:
            value = 'json' in mime.lower() and self._insertId(stream.read(length), os.path.basename(key)) or stream.read(length)
        except ValueError:
            raise KeyError, 'not a valid JSON'

        with self.lock:            
            self.data[key] = value
            self.data.sync()

    def _insertId(self, value, key):
        obj = json.loads(value)
        obj['id'] = key
        return json.dumps(obj)

        
    def delete(self, key):
        del self.data[key]

    def new(self, parent, title, mime):
        newid = self._title2id(title, mime)
        n = 1
        path = os.path.join(parent, newid)
        p,e = os.path.splitext(path)
        while path in self.data:
            path = ''.join([p, str(n), e])
            n +=1
        newid = os.path.basename(path)
        self.data[path] = None
        return newid

    def mime(self, key):
        if key in self.data:
            return mimetypes.guess_type(key)[0] or 'application/octet-stream'
        raise KeyError, 'not found'

    def etag(self, key):
        return md5(self.data[key]).hexdigest()

    def close(self):
        self.data.close()
        

        
