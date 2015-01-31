# -*- coding: utf-8 -*-
import shlex
import re

from twisted.internet.protocol import ClientFactory
from twisted.words.protocols.irc import IRCClient
from twisted.python import log

from bottu import flags
from bottu.utils import Queued


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

    def is_active(self):
        return self.name[1:] in self.client.app.channels


class MultiChannel(object):
    def __init__(self, client, channels):
        self.client = client
        self.channels = channels

    def msg(self, message):
        for channel in self.channels:
            channel.msg(message)


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
        self.signed_on = False
        self._active_channels = MultiChannel(self, [])

    def _fire_event(self, name, user=None, channel=None, *args, **kwargs):
        if channel and not channel.is_active():
            target = self._active_channels
        else:
            target = None
        self.app.fire_event(
            name, user=user, channel=channel, target=target, *args, **kwargs
        )

    def get_nickname(self):
        return self.app.name

    def set_nickname(self, val):
        self.app.name = val
    nickname = property(get_nickname, set_nickname)

    def signedOn(self):
        self.signed_on = True
        self._active_channels = MultiChannel(
            self,
            [Channel(self, '#%s' % name) for name in self.app.channels]
        )
        log.msg("signed on")
        for channel in self.app.channels:
            self.join(channel)
            self.sendLine('NAMES %s' % channel)
        self.join.ready()
        self.msg.ready()

    @Queued()
    def msg(self, user, message, length=None):
        """
        Send a message to a channel, enforces message encoding
        """
        encoded_message = unicode(message).encode('ascii', 'ignore')
        if user.startswith('#') and not Channel(self, user).is_active():
            log.msg(
                "ERROR: Trying to send message to inactive channel %s. "
                "Message blocked!" % user
            )
        else:
            log.msg("Sending %r to %r" % (encoded_message, user))
            IRCClient.msg(self, user, encoded_message, length)

    @Queued()
    def join(self, channel, key=None):
        log.msg("Joining %r" % channel)
        IRCClient.join(self, channel, key)

    def joined(self, rawchannel):
        """
        After the bot joined a channel
        """
        log.msg("joined: %s" % rawchannel)
        channel = Channel(self, rawchannel)
        self._fire_event('joined', channel=channel)

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
            self._fire_event(
                'message',
                user=user,
                channel=channel,
                message=message
            )
        if channel is None or channel.is_active():
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

    def userJoined(self, rawuser, rawchannel):
        log.msg("User %r joined %r" % (rawuser, rawchannel))
        channel = Channel(self, rawchannel)
        user = User(self, rawuser)
        self._fire_event('user_joined', channel=channel, user=user)

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
        self.proto = None
        self._queue = []

    @Queued()
    def join(self, channel):
        self.proto.join(channel)

    def buildProtocol(self, addr):
        log.msg("Building protocol for %r" % addr)
        proto = ClientFactory.buildProtocol(self, addr)
        proto.app = self.app
        proto.password = self.app.password
        self.proto = proto
        self.join.ready()
        return proto

    def clientConnectionLost(self, connector, reason):
        log.msg("connection lost, reconnecting...")
        connector.connect()
