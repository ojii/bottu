# -*- coding: utf-8 -*-
from argparse import ArgumentParser

from twisted.python import log


class ArgumentParserError(Exception):
    def __init__(self, message):
        self.message = message


class IRCArgumentParser(ArgumentParser):
    def error(self, message):
        raise ArgumentParserError(message)


class Command(object):
    def __init__(self, plugin, name, help_text, prefix):
        self.plugin = plugin
        self.name = name
        self.help_text = help_text
        self.arg_parser = IRCArgumentParser(
            add_help=False,
            description=self.help_text,
            prog='{prefix}{name}'.format(
                prefix=prefix,
                name=name,
            )
        )
        self.guards = []
        self.callbacks = []

    def add_argument(self, *args, **kwargs):
        self.arg_parser.add_argument(*args, **kwargs)

    def guard(self, permission):
        self.guards.append(permission)

    def bind(self, callback):
        self.callbacks.append(callback)

    def execute(self, env, args):
        if not self.plugin.active:
            log.msg("Plugin inactive, suppressing command")
            return
        for guard in self.guards:
            if not guard.check(env):
                env.msg("Permission denied!")
                return
        try:
            kwargs = vars(self.arg_parser.parse_args(args))
        except ArgumentParserError as exc:
            env.msg('Error: %s' % exc.message)
            log.msg(self.arg_parser.usage)
            return
        log.msg("Got kwargs %r" % kwargs)
        for callback in self.callbacks:
            try:
                callback(env, **kwargs)
            except Exception:
                log.err()
