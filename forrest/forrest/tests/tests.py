import unittest
import os.path
from forrest.resources import fs, filedict, ramdict
from forrest import app
from StringIO import StringIO

class MockResource(object):
    def new(self, parent, title, mime):
        if parent == 'folder':
            return 'test.txt'
        raise KeyError
    def mime(self, key):
        return 'text/plain'
    def etag(self, key):
        return "etag"
    def get(self, key):
        if key == 'test.txt':
            return StringIO('test.txt'), 8
        raise KeyError
    def set(self, key, stream, length):
        if key != 'test.txt':
            raise KeyError
    def delete(self, key):
        if key != 'test.txt':
            raise KeyError


def consumeapp(app, environ):
    data = {}
    def get_start_response(data):
        def start_response(status, headers):
            data['status'] = status
            data['headers'] = dict(headers)
        return start_response

    start_response = get_start_response(data)
    text = ''.join([chunk for chunk in app(environ, start_response)])
    return {'status':data['status'],'headers':data['headers'],'content':text}

class TestWsgiApp(unittest.TestCase):
    def setUp(self):
        self.app = app.RestApp({'resources':MockResource()})

    def testGet(self):
        """ get"""
        output = consumeapp(self.app,{"REQUEST_METHOD":'GET', 'PATH_INFO':'test.txt'})
        self.assertEquals(output['status'], '200 OK')
        self.assertEquals(output['content'], 'test.txt')
        self.assertEquals(output['headers']['Content-Length'], '8')
        self.assertEquals(output['headers']['Content-Type'], 'text/plain')
        self.assertEquals(output['headers']['ETag'], 'etag')

    def testGet404(self):
        """ get 404"""
        output = consumeapp(self.app,{"REQUEST_METHOD":'GET', 'PATH_INFO':'not exist.txt'})
        self.assertEquals(output['status'], '404 NOT FOUND')
        self.assertEquals(output['content'], 'Not Found')
        self.assertEquals(output['headers']['Content-Length'], '9')
        self.assertEquals(output['headers']['Content-Type'], 'text/plain')
        self.assertTrue('ETag' not in output['headers'])

    def testGet304(self):
        """ get not modified"""
        output = consumeapp(self.app,{"REQUEST_METHOD":'GET', 'PATH_INFO':'test.txt', 'HTTP_IF_NONE_MATCH':'etag'})

        self.assertEquals(output['status'], '304 Not Modified')
        self.assertEquals(output['content'], 'Not Modified')
        self.assertEquals(output['headers']['Content-Length'], '12')
        self.assertEquals(output['headers']['Content-Type'], 'text/plain')
        self.assertTrue('ETag' not in output['headers'])

    def testPut(self):
        """put"""
        output = consumeapp(self.app,{"REQUEST_METHOD":'PUT', 'PATH_INFO':'test.txt', 'wsgi.input':StringIO('new'),'CONTENT_LENGTH':'3'})
        self.assertEquals(output['status'], '200 OK')
        self.assertEquals(output['content'], 'ok')
        self.assertTrue(output['headers']['Content-Length'], '2')
        self.assertEquals(output['headers']['Content-Type'], 'text/plain')
        self.assertTrue('ETag' not in output['headers'])

    def testPut404(self):
        """put 404"""
        output = consumeapp(self.app,{"REQUEST_METHOD":'PUT', 'PATH_INFO':'not exists.txt', 'wsgi.input':StringIO('new'),'CONTENT_LENGTH':'3'})
        self.assertEquals(output['status'], '404 NOT FOUND')
        self.assertEquals(output['content'], 'Not Found')
        self.assertEquals(output['headers']['Content-Length'], '9')
        self.assertEquals(output['headers']['Content-Type'], 'text/plain')
        self.assertTrue('ETag' not in output['headers'])

    def testPutNot412(self):
        """put etag"""
        output = consumeapp(self.app,{"REQUEST_METHOD":'PUT', 'PATH_INFO':'test.txt', 'wsgi.input':StringIO('new'),'CONTENT_LENGTH':'3', 'HTTP_IF_MATCH':'etag'})
        self.assertEquals(output['status'], '200 OK')
        self.assertEquals(output['content'], 'ok')
        self.assertTrue(output['headers']['Content-Length'], '2')
        self.assertEquals(output['headers']['Content-Type'], 'text/plain')
        self.assertTrue('ETag' not in output['headers'])

    def testPut412(self):
        """put etag"""
        output = consumeapp(self.app,{"REQUEST_METHOD":'PUT', 'PATH_INFO':'test.txt', 'wsgi.input':StringIO('new'),'CONTENT_LENGTH':'3', 'HTTP_IF_MATCH':'xxxetag'})
        self.assertEquals(output['status'], '412 Precondition Failed')
        self.assertEquals(output['content'], 'Precondition Failed')
        self.assertTrue(output['headers']['Content-Length'], '19')
        self.assertEquals(output['headers']['Content-Type'], 'text/plain')

    def testDelete(self):
        """DELETE"""
        output = consumeapp(self.app,{"REQUEST_METHOD":'DELETE', 'PATH_INFO':'test.txt'})
        self.assertEquals(output['status'], '200 OK')
        self.assertEquals(output['content'], 'ok')
        self.assertTrue(output['headers']['Content-Length'], '2')
        self.assertEquals(output['headers']['Content-Type'], 'text/plain')
        self.assertTrue('ETag' not in output['headers'])

    def testDelete404(self):
        """DELETE 404"""
        output = consumeapp(self.app,{"REQUEST_METHOD":'DELETE', 'PATH_INFO':'not exists.txt'})
        self.assertEquals(output['status'], '404 NOT FOUND')
        self.assertEquals(output['content'], 'Not Found')
        self.assertEquals(output['headers']['Content-Length'], '9')
        self.assertEquals(output['headers']['Content-Type'], 'text/plain')
        self.assertTrue('ETag' not in output['headers'])

    def testDeleteNot412(self):
        """DELETE etag"""
        output = consumeapp(self.app,{"REQUEST_METHOD":'DELETE', 'PATH_INFO':'test.txt','HTTP_IF_MATCH':'etag'})
        self.assertEquals(output['status'], '200 OK')
        self.assertEquals(output['content'], 'ok')
        self.assertTrue(output['headers']['Content-Length'], '2')
        self.assertEquals(output['headers']['Content-Type'], 'text/plain')
        self.assertTrue('ETag' not in output['headers'])

    def testDelete412(self):
        """DELETE etag"""
        output = consumeapp(self.app,{"REQUEST_METHOD":'DELETE', 'PATH_INFO':'test.txt','HTTP_IF_MATCH':'xxxetag'})
        self.assertEquals(output['status'], '412 Precondition Failed')
        self.assertEquals(output['content'], 'Precondition Failed')
        self.assertTrue(output['headers']['Content-Length'], '19')
        self.assertEquals(output['headers']['Content-Type'], 'text/plain')

    def testPost(self):
        """post"""
        output = consumeapp(self.app,{"REQUEST_METHOD":'POST', 'PATH_INFO':'folder', 'wsgi.input':StringIO('new'),'CONTENT_LENGTH':'3', 'SLUG':'test.txt'})
        self.assertEquals(output['status'], '201 Created')
        self.assertEquals(output['content'], '{"id":"test.txt"}')
        self.assertTrue(output['headers']['Content-Length'], '17')
        self.assertEquals(output['headers']['Content-Type'], 'application/json')
        self.assertEquals(output['headers']['Location'], 'test.txt')
        
    def testPost404(self):
        """post 404"""
        output = consumeapp(self.app,{"REQUEST_METHOD":'POST', 'PATH_INFO':'wrong_folder', 'wsgi.input':StringIO('new'),'CONTENT_LENGTH':'3', 'SLUG':'test.txt'})
        self.assertEquals(output['status'], '404 NOT FOUND')
        self.assertEquals(output['content'], 'Not Found')
        self.assertEquals(output['headers']['Content-Length'], '9')
        self.assertEquals(output['headers']['Content-Type'], 'text/plain')
        self.assertTrue('ETag' not in output['headers'])

class TestBaseDict(unittest.TestCase):

    def testGetResource(self):
        self.assertEqual(self.d.get('test.txt')[0].read(), 'this is a test')
        self.assertTrue(self.d.etag('test.txt'))
        self.assertEqual(self.d.mime('test.txt'), 'text/plain')

        with self.assertRaises(KeyError):
            s = self.d.get('notexists.txt')
        with self.assertRaises(KeyError):
            s = self.d.mime('notexists.txt')
        with self.assertRaises(KeyError):
            s = self.d.etag('notexists.txt')

    def testCannotDelete(self):
        with self.assertRaises(KeyError):
            self.d.delete('notexists.txt')
        with self.assertRaises(KeyError):
            self.d.delete('folder')

    def testPut(self):
        with self.assertRaises(KeyError):
            self.d.set('notexists.txt', StringIO('raise error'), len('raise error'))
        with self.assertRaises(KeyError):
            self.d.set('folder', StringIO('raise error again'), len('raise error again'))

        etag = self.d.etag('test.txt')
        original_stream, original_l = self.d.get('test.txt')

        original_content = original_stream.read(original_l)
        self.d.set('test.txt', StringIO('this is a new string'), len('this is a new string'))
        self.assertTrue(etag != self.d.etag('test.txt'))
        self.assertTrue(self.d.get('test.txt')[0].read() == 'this is a new string')
        self.d.set('test.txt', StringIO(original_content), len(original_content))
        self.assertTrue(etag == self.d.etag('test.txt'))
        self.assertTrue(self.d.get('test.txt')[0].read() == original_content)
        

    def testNewPutDelete(self):
        with self.assertRaises(KeyError):
            self.d.set('folder/xxx.js', StringIO('raise error'), len('raise error'))

        newid = self.d.new('folder', 'xxx', 'application/javascript')

        newid2 = self.d.new('folder', 'xxx', 'application/javascript')
        newid3 = self.d.new('folder', 'xxx', 'application/javascript')

        self.assertEquals(newid,'xxx.js')
        self.assertEquals(newid2,'xxx1.js')
        self.assertEquals(newid3,'xxx2.js')
        self.d.set('folder/xxx.js', StringIO('new text'), len('new text'))
        self.d.delete('folder/xxx.js')
        with self.assertRaises(KeyError):
            s = self.d.get('folder/xxx.js')
        

class TestRamDict(TestBaseDict):
    def setUp(self):
        self.d = ramdict.RamDict()
        self.d.data['test.txt'] = 'this is a test'

        

class TestFileDict(TestBaseDict):

    def setUp(self):
        os.remove('test.dat')
        self.d = filedict.FileDict('test.dat')
        self.d.data['test.txt'] = 'this is a test'

    def tearDown(self):
        self.d.close()


class TestFs(unittest.TestCase):

    def setUp(self):
        path = os.path.join(os.path.dirname(__file__), 'resources')
    
        self.d = fs.FileSystem(path)
        
    def testGetResource(self):
        self.assertEqual(self.d.get('test.txt')[0].read(), 'this is a test\n')
        self.assertTrue(self.d.etag('test.txt'))
        self.assertEqual(self.d.mime('test.txt'), 'text/plain')

        with self.assertRaises(KeyError):
            s = self.d.get('notexists.txt')
        with self.assertRaises(KeyError):
            s = self.d.mime('notexists.txt')
        with self.assertRaises(KeyError):
            s = self.d.etag('notexists.txt')

    def testGetCollection(self):
        import json
        self.assertTrue(json.load(self.d.get('')[0])[0]['mimetype'] == 'text/plain')
        self.assertTrue(json.load(self.d.get('')[0])[0]['id'] == 'test.txt')
        self.assertTrue(self.d.etag('folder') == None)
        self.assertEqual(self.d.mime('folder'), 'application/json')
        for item in json.load(self.d.get('folder')[0]):
            self.assertTrue(item['id'] in ['file1.txt', 'file1.json', 'file2.json'])
            if item['id'] == 'file1.txt':
                self.assertEquals(item['mimetype'],'text/plain')
            elif item['id'] == 'file1.json':
#                self.assertEquals(item['mimetype'],'application/json')
                self.assertEquals(item['greetings'],'hello')
            elif item['id'] == 'file2.json':
#                self.assertEquals(item['mimetype'],'application/json')
                self.assertEquals(item['greetings'],'goodbye')

    def testCannotDelete(self):
        with self.assertRaises(KeyError):
            self.d.delete('notexists.txt')
        with self.assertRaises(KeyError):
            self.d.delete('folder')

    def testPut(self):
        with self.assertRaises(KeyError):
            self.d.set('notexists.txt',StringIO('raise error'),11)
        with self.assertRaises(KeyError):
            self.d.set('folder',StringIO('raise error'),11)

        etag = self.d.etag('test.txt')
        original_stream, original_l = self.d.get('test.txt')
        with original_stream:
            original_content = original_stream.read(original_l)

        self.d.set('test.txt', StringIO('this is a new string'),len('this is a new string'))
        self.assertTrue(etag != self.d.etag('test.txt'))
        self.assertTrue(self.d.get('test.txt')[0].read() == 'this is a new string')
        self.d.set('test.txt',StringIO(original_content), original_l)
        self.assertTrue(etag == self.d.etag('test.txt'))
        self.assertTrue(self.d.get('test.txt')[0].read() == original_content)
        

    def testNewPutDelete(self):
        with self.assertRaises(KeyError):
            self.d.new('notexist', 'xxx', 'text/javascript')
        with self.assertRaises(KeyError):
            self.d.set('folder/xxx.js',StringIO('raise error'), len('raise error'))

        newid = self.d.new('folder', 'xxx', 'application/javascript')

        newid2 = self.d.new('folder', 'xxx', 'application/javascript')
        newid3 = self.d.new('folder', 'xxx', 'application/javascript')

        self.assertEquals(newid,'xxx.js')
        self.assertEquals(newid2,'xxx1.js')
        self.assertEquals(newid3,'xxx2.js')
        self.d.set('folder/xxx.js', StringIO('new'), len('new'))
        self.d.delete('folder/xxx.js')
        with self.assertRaises(KeyError):
            s = self.d.get('folder/xxx.js')
        
        #get
   
#def suite():
#    suite = unittest.TestSuite()
#    suite.addTest(unittest.makeSuite(TestGet))
#    suite.addTest(unittest.makeSuite(TestPost))
#    return suite

#if __name__ == '__main__':

##    runner = unittest.TextTestRunner()
#    test_suite = suite()
#    test_suite.run()

