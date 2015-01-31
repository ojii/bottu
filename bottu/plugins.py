# -*- coding: utf-8 -*-
# Copyright (c) 2012, Jonas Obrist
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the Jonas Obrist nor the
#      names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL JONAS OBRIST BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import pkg_resources

from bottu import flags
from bottu.command import Command
from bottu.permissions import Permission


class Plugin(object):
    def __init__(self, app, name):
        self.app = app
        self.name = name
        self.active = True

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False

    def add_command(self, name, help_text):
        if name in self.app.commands:
            raise ValueError("Command with name %r already registered." % name)
        command = Command(self, name, help_text, self.app.command_prefix)
        self.app.commands[name] = command
        return command

    def add_permission(self, name, default=flags.NONE):
        if '|' in name:
            raise ValueError("Permission names cannot contain :")
        if name in self.app.permissions:
            raise ValueError("Permission with name %r already registered." % name)
        permission = Permission(self, name, default)
        self.app.permissions[name] = permission
        return permission

    def bind_event(self, name, callback):
        self.app.bind_event(name, callback, self)


def load_plugins(app):
    for entry_point in pkg_resources.iter_entry_points('bottu.plugins'):
        plugin = entry_point.load()
        conf = app.pluginconf.get(entry_point.name, {})
        plugin(app, conf)
