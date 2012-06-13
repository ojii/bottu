# -*- coding: utf-8 -*-
from bottu.environment import Environment
from bottu.irc import User


def help(env, key=None):
    pass

def grant(env, user, permission):
    if permission == '*':
        permissions = env.app.permissions.keys()
    else:
        permissions = [permission]
    for perm in permissions:
        try:
            env.app.permissions[perm].grant(user)
        except KeyError:
            env.msg("Permission %s not found" % perm)
            return
        env.msg("Granted %s permission %s" % (user, perm))

def revoke(env, user, permission):
    if permission == '*':
        permissions = env.app.permissions.keys()
    else:
        permissions = [permission]
    for perm in permissions:
        try:
            env.app.permissions[perm].revoke(user)
        except KeyError:
            env.msg("Permission %s not found" % perm)
            return
        env.msg("Revoked %s permission %s" % (user, perm))

def permissions(env, username):
    perms = []
    userenv = Environment(env.app, env.plugin, User(env.user.client, username), None)
    for permission in env.app.permissions.values():
        if permission.check(userenv):
            perms.append(permission.name)
    env.msg("%s has following permissions: %s" % (username, ', '.join(perms)))

def listperms(env):
    env.msg("Available permissions: %s" % ', '.join(env.app.permissions.keys()))

def register(app):
    #help_plugin = app.add_plugin("Help")
    perms_plugin = app.add_plugin("Permissions")
    admin = perms_plugin.add_permission('admin')

    grant_cmd = perms_plugin.add_command('grant', 'Grant a user permission')
    grant_cmd.add_argument('user')
    grant_cmd.add_argument('permission')
    grant_cmd.guard(admin)
    grant_cmd.bind(grant)

    revoke_cmd = perms_plugin.add_command('revoke', 'Revoke a user permission')
    revoke_cmd.add_argument('user')
    revoke_cmd.add_argument('permission')
    revoke_cmd.guard(admin)
    revoke_cmd.bind(revoke)

    deny_cmd = perms_plugin.add_command('permissions', 'Show what permissions a user has')
    deny_cmd.add_argument('username')
    deny_cmd.guard(admin)
    deny_cmd.bind(permissions)

    listperms_cmd = perms_plugin.add_command('listperms', 'Show available permissions')
    listperms_cmd.guard(admin)
    listperms_cmd.bind(listperms)
