# -*- coding: utf-8 -*-namespace
class Environment(object):
    def __init__(self, app, plugin, user, channel):
        self.app = app
        self.plugin = plugin
        self.prefix = self.plugin.name
        self.user = user
        self.channel = channel
        self.target = self.channel or self.user

    # IRC API

    def msg(self, message):
        self.target.msg(message)

    # Storage API

    def get(self, key, default=None):
        return self.app.storage.get(self.prefix, key, default)

    def store(self, key, value):
        return self.app.storage.store(self.prefix, key, value)

    def delete(self, key):
        return self.app.storage.delete(self.prefix, key)

    def keys(self):
        return self.app.storage.keys(self.prefix)
