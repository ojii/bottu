# -*- coding: utf-8 -*-
import shlex
from bottu import flags
import re
from twisted.internet.protocol import ClientFactory
from twisted.words.protocols.irc import IRCClient
from twisted.python import log


MODE_RE = re.compile(r'(?:(?P<op>@)|(?P<voice>\+))?(?P<nick>.+)')


def split_user_mode(user):
    match = MODE_RE.match(user)
    if not match:
        return flags.ALL
    gd = match.groupdict()
    nick = gd['nick']
    if gd['op']:
        return nick, flags.OPERATOR
    elif gd['voice']:
        return nick, flags.VOICE
    else:
        return nick, flags.ALL


class Channel(object):
    def __init__(self, client, name):
        self.client = client
        self.name = name

    def msg(self, message):
        self.client.msg(self.name, message)


class User(Channel):
    @property
    def level(self):
        return self.client.level(self.name)


class BottuClient(IRCClient):
    """
    The IRC bot protocol
    """
    def __init__(self):
        self.user_mode_cache = {}

    def get_nickname(self):
        return self.app.name

    def set_nickname(self, val):
        self.app.name = val
    nickname = property(get_nickname, set_nickname)

    def signedOn(self):
        log.msg("signed on")
        for channel in self.app.channels:
            self.join(channel)
            self.sendLine('NAMES %s' % channel)

    def msg(self, user, message, length=None):
        """
        Send a message to a channel, enforces message encoding
        """
        encoded_message = unicode(message).encode('ascii', 'ignore')
        log.msg("Sending %r to %r" % (encoded_message, user))
        IRCClient.msg(self, user, encoded_message, length)

    def joined(self, rawchannel):
        """
        After the bot joined a channel
        """
        log.msg("joined: %s" % rawchannel)
        channel = Channel(self, rawchannel)
        self.app.fire_event('joined', channel=channel)

    def privmsg(self, rawuser, rawchannel, message):
        """
        When the bot receives a privmsg (from a user or channel)
        """
        log.msg("Handling privmsg %r %r %r" % (rawuser, rawchannel, message))
        # check for private message
        nick = rawuser.split('!')[0]
        user = User(self, nick)
        if rawchannel == self.nickname:
            channel = None
        else:
            channel = Channel(self, rawchannel)
            self.app.fire_event('message', user=user, channel=channel, message=message)
        try:
            bits = shlex.split(message)
        except ValueError:
            bits = message.split(' ')
        command_name = bits.pop(0) if bits else None
        if command_name and command_name.startswith(self.app.command_prefix):
            command_name = command_name[1:]
            self.app.call_command(command_name, channel, user, bits)

    def irc_unknown(self, prefix, command, params):
        """
        Unknown (to twisted) IRC command, the response to the NAMES query we
        do in signedOn
        """
        log.msg("Handling unknown IRC command: %r %r %r" % (prefix, command, params))
        if command == 'RPL_NAMREPLY':
            self.handle_namereply(*params)

    def handle_namereply(self, myname, channeltype, channelname, users):
        """
        Handles a RPL_NAMREPLY command, caches user modes
        """
        log.msg("Handling namereploy %r %r %r %r" % (myname, channeltype, channelname, users))
        for user in users.split(' '):
            nick, mode = split_user_mode(user)
            self.user_mode_cache[nick] = mode

    def userRenamed(self, old, new):
        """
        When a user is renamed, re-cache permissions
        """
        log.msg("User renamed %r->%r" % (old, new))
        self.user_mode_cache[new] = self.user_mode_cache.pop(old, flags.ALL)

    def userLeft(self, user, channel):
        """
        When a user leaves a channel, remove user mode cache
        """
        nick = user.split('!')[0]
        log.msg("User left %r" % nick)
        self.user_mode_cache.pop(nick, None)

    def modeChanged(self, user, channel, set_mode, modes, args):
        """
        When a user mode changes, re-cache permissions
        """
        log.msg("Mode changed: %r %r %r %r %r" % (user, channel, set_mode, modes, args))
        nick = args[0] if len(args) == 1 else None
        if 'o' in modes:
            if set_mode:
                self.user_mode_cache[nick] = flags.OPERATOR
            elif not set_mode:
                self.user_mode_cache[nick] = flags.ALL
        elif 'v' in modes:
            if set_mode:
                self.user_mode_cache[nick] = flags.VOICE
            elif not set_mode:
                self.user_mode_cache[nick] = flags.ALL

    def level(self, nick):
        return self.user_mode_cache.get(nick, flags.ALL)


class BottuClientFactory(ClientFactory):
    protocol = BottuClient

    def __init__(self, app):
        self.app = app

    def buildProtocol(self, addr):
        log.msg("Building protocol for %r" % addr)
        proto = ClientFactory.buildProtocol(self, addr)
        proto.app = self.app
        return proto

    def clientConnectionLost(self, connector, reason):
        log.msg("connection lost, reconnecting...")
        connector.connect()
