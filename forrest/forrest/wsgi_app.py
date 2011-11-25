from app import RestApp

#.ini
# resource_class=somepackage.somemodule:someclass
# example:
# resource_class=forrest.resources.filedict:FileDict
# resource_class=forrest.resources.fs:FileSystem
# resource_class=forrest.resources.fs:RamDict

def make_app(global_conf, resource_class, **kw):

    from paste.util.import_string import eval_import
    import types

    conf = global_conf.copy()
    conf.update(kw)
    Resources = eval_import(resource_class)
    assert isinstance(Resources, types.TypeType), "resource_class must resolve to a function"
    conf['resources'] = Resources(**conf)
    return RestApp(conf)


