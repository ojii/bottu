# -*- coding: utf-8 -*-
from collections import defaultdict

from twisted.python import log
from twisted.internet import reactor

from bottu import builtin_commands
from bottu.events import Event
from bottu.irc import BottuClientFactory
from bottu.environment import Environment
from bottu.plugins import load_plugins, Plugin
from bottu.utils import Queued, CaseInsensitiveDict


class RedisStorage(object):
    def __init__(self, app):
        import redis
        self.app = app
        self.redis = redis.from_url(app.redis_dsn)

    def store(self, namespace, key, value):
        return self.redis.hset(namespace, key, value)

    def get(self, namespace, key, default=None):
        return self.redis.hget(namespace, key) or default

    def delete(self, namespace, key):
        return self.redis.hdel(namespace, key)

    def keys(self, namespace):
        return self.redis.hkeys(namespace)


class Application(object):
    def __init__(self, name, channels, network, port, redis_dsn,
                 command_prefix='!', pluginconf=None, password=None):
        log.msg("Initializing")
        self.name = name
        self.channels = channels
        self.network = network
        self.port = port
        self.redis_dsn = redis_dsn
        self.command_prefix = command_prefix
        self.pluginconf = pluginconf or {}
        self.password = password
        self.commands = {}
        self.permissions = {}
        self.plugins = CaseInsensitiveDict()
        self.events = defaultdict(Event)
        self.irc = None
        log.msg("Loading builtin plugins")
        builtin_commands.register(self)
        log.msg("Loading custom plugins")
        load_plugins(self)
        log.msg("All plugins loaded")
        log.msg("Attaching storage")
        self.storage = RedisStorage(self)
        log.msg("Attached storage")

    def bind_event(self, name, callback, plugin):
        log.msg(
            "Binding event %r with callback %r from %r" % (
                name, callback, plugin
            )
        )
        self.events[name].bind(callback, plugin)

    def fire_event(self, name, user=None, channel=None, target=None,
                   *args, **kwargs):
        if channel and not channel.is_active():
            name += '_passive'
        log.msg(
            "Firing event %r for user %r / channel %r, with args %r and "
            "kwargs %r" % (name, user, channel, args, kwargs)
        )
        self.events[name].fire(self, user, channel, target, *args, **kwargs)

    def call_command(self, command_name, channel, user, bits):
        log.msg(
            "Calling command %r for channel %r/user %r, with args %r" % (
                command_name, channel, user, bits
            )
        )
        command = self.commands.get(command_name, None)
        if command:
            env = Environment(self, command.plugin, user, channel)
            command.execute(env, bits)
        else:
            log.msg("Command not found")
            log.msg(self.commands.keys())

    def add_plugin(self, name):
        log.msg("Adding plugin %r" % name)
        if name.startswith('~'):
            # internal namespace
            raise ValueError("Plugin names may not start with a ~")
        if name in self.plugins:
            raise ValueError("Plugin with name %r already loaded" % name)
        plugin = Plugin(self, name)
        self.plugins[name] = plugin
        return plugin

    def grant_permission(self, username, permission):
        self.permissions[permission].grant(username)

    def revoke_permission(self, username, permission):
        self.permissions[permission].revoke(username)

    @Queued()
    def join_passive_channel(self, channel):
        return self.irc.join(channel)

    def run(self):
        log.msg("Running bot as %r" % self.name)
        self.irc = BottuClientFactory(self)
        self.join_passive_channel.ready()
        reactor.connectTCP(self.network, self.port, self.irc)
        reactor.run()
        log.msg("Stopping bot")
