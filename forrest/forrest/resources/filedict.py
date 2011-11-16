import shelve
from hashlib import md5
import mimetypes
import os.path
import threading
from StringIO import StringIO
from forrest.app import RestApp
from contextlib import closing

class FileDict(object):
    def __init__(self, **config):
        self.root = config['path']
        self.data = shelve.open(self.root)
        self.lock = threading.Lock()


    def _title2id(self, title, mime):
        if not title:
            return 'item'
        if not isinstance(title, unicode):
            title = unicode(title, 'utf-8')
        s = title.encode('ascii', 'ignore')
        s = s.translate(None,'''!"#$%&\'()*+,/:;<=>?@[\\]^`{|}~''')
        extension = mimetypes.guess_extension(mime) or ""
        return "-".join(s.split()) + extension

    def get(self, key, options=None):
        value = self.data[key]
        return StringIO(value), len(value)
            
    def set(self, key, stream, length):
        if key not in self.data:
            raise KeyError, 'not found'

        with closing(stream):
            value = stream.read(length)
        with self.lock:            
            self.data[key] = value
            self.data.sync()
        
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
            return mimetypes.guess_type(key)[0]
        raise KeyError, 'not found'

    def etag(self, key):
        return md5(self.data[key]).hexdigest()

    def close(self):
        self.data.close()
        

        
