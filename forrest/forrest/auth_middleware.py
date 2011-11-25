from hashlib import md5

# anon
def splitlist(l, sep=':'):
    return [item.strip() for item in l.split(sel)]

class Auth(object):
    """add the permission vocab in the environ"""
    PERMISSIONS = set(['get', 'post', 'put', 'delete'])
    def __init__(self, app, users, rules):
        self.users = {}
        self.groups = {}
        allgroups = []
        for row in users:
            u, p, groups = row.split(':')
            uname = u.strip()
            self.users[uname] = p.strip()
            self.groups[uname] = set(groups.split())
            allgroups += self.groups[uname]

        allgroups = set(allgroups)

        self.rules = []
        for row in rules:
            url, p, g = row.split(':')
            if '*' in p:
                permissions = self.PERMISSIONS
            else:
                permissions = set([perm for perm in p.lower().split() if perm in self.PERMISSIONS])
            
            if '*' in g:
                groups = allgroups
            else:
                groups = set(g.split())
            
            self.rules.append([url.strip(), permissions, groups])

        self.app = app
        
        #
    def __call__(self, environ, start_response):
        environ['AUTH.USERS'] = self.users
        environ['AUTH.GROUPS'] = self.groups
        environ['AUTH.RULES'] = self.rules
        return self.app(environ, start_response)

def make_auth_middleware(app, global_conf, users, rules, **kw):
    """
    Populate the auth dict

    Config looks like this::

    [filter:auth]
    use = egg:forrest#auth
    filter-with = basic
    users =
    rules =
      
    """
    return Auth(app, users.strip().splitlines(), rules.strip().splitlines())
    

def auth(env, user, password):
    """called the basic paste plugin and use the in the environ"""
    users = env.get('AUTH.USERS', {})
    groups = env.get('AUTH.GROUPS', {})
    rules = env.get('AUTH.RULES', [])

    # check user/password
    if user not in users or users[user] != md5(password).hexdigest():
        return False

    usergroups = groups.get(user, set())

    method = env.get("X-HTTP-METHOD-OVERRIDE")
    if not method:
        method = env["REQUEST_METHOD"]

    for url, permissions, groups in rules:
        if env['PATH_INFO'].startswith(url) and len(groups & usergroups) and method.lower() in permissions:
            return True
    return False
    


