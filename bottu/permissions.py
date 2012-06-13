# -*- coding: utf-8 -*-
from bottu import flags
from twisted.python import log


class Permission(object):
    def __init__(self, plugin, name, default=flags.NONE):
        self.plugin = plugin
        self.app = self.plugin.app
        self.name = name
        self.default = default

    def check(self, env):
        if not env.user: # wtf, should never happen!!
            log.msg("No user, no idea how this happened, deny permission.")
            return False
        log.msg("Checking user level %s against default %s" % (env.user.level, self.default))
        if isinstance(env.user.level, self.default): # default guard
            log.msg("User matches default permission level")
            return True
        key = self.key(env.user.name)
        log.msg("Checking for permission key %r in ~perms" % key)
        result =  self.app.storage.get('~perms', key, False)
        log.msg("Permission for key %r in ~perms: %s" % (key, result))
        return result

    def key(self, username):
        return '%s:%s:%s' % (username, self.plugin.name, self.name)

    def grant(self, username):
        return self.app.storage.store('~perms', self.key(username), True)

    def revoke(self, username):
        return self.app.storage.delete('~perms', self.key(username))
