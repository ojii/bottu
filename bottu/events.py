# -*- coding: utf-8 -*-
from twisted.python import log

from bottu.environment import Environment


class Event(object):
    def __init__(self):
        self.callbacks = []

    def bind(self, callback, plugin):
        self.callbacks.append((callback, plugin))

    def fire(self, app, user, channel, target, *args, **kwargs):
        for callback, plugin in self.callbacks:
            if not plugin.active:
                continue
            env = Environment(app, plugin, user, channel, target)
            try:
                callback(env, *args, **kwargs)
            except Exception:
                log.err()
