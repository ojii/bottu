# -*- coding: utf-8 -*-
from bottu.environment import Environment
from twisted.python import log


class Event(object):
    def __init__(self):
        self.callbacks = []

    def bind(self, callback, plugin):
        self.callbacks.append((callback, plugin))

    def fire(self, app, user, channel, *args, **kwargs):
        for callback, plugin in self.callbacks:
            env = Environment(app, plugin, user, channel)
            try:
                callback(env, *args, **kwargs)
            except Exception:
                log.err()
