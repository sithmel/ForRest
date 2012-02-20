Forrest package
------------------

A wsgi app serving a portion of file system with a restful interface.
Designed to work with Backbone.js and with other libraries.

TODO:
- manage the accept header:
   if accept == application/json:
       if content == json: send json
       else: send a json rappresentation of the obj
   else:
       if content == json: send html (template + data  json)
       else: send content
