# -*- coding: utf-8 -*-
from bottu.environment import Environment
from bottu.irc import User


def show_help(env, command=None):
    if command:
        try:
            cmd = env.app.commands[command]
        except KeyError:
            env.msg("Command not found: %s" % command)
            return
        lines = (
            line.rstrip()
            for line in cmd.arg_parser.format_help().split('\n')
            if line.strip()
        )
        for line in lines:
            env.msg(line)
    else:
        available_commands = sorted(env.app.commands.keys())
        env.msg("Available commands: {commands}".format(
            commands=', '.join(available_commands)
        ))


def grant(env, user, permission):
    if permission == '*':
        perms = env.app.permissions.keys()
    else:
        perms = [permission]
    for perm in perms:
        try:
            env.app.grant_permission(user, permission)
        except KeyError:
            env.msg("Permission %s not found" % perm)
            return
        env.msg("Granted %s permission %s" % (user, perm))


def revoke(env, user, permission):
    if permission == '*':
        perms = env.app.permissions.keys()
    else:
        perms = [permission]
    for perm in perms:
        try:
            env.app.revoke_permission(user, perm)
        except KeyError:
            env.msg("Permission %s not found" % perm)
            return
        env.msg("Revoked %s permission %s" % (user, perm))


def permissions(env, username):
    perms = []
    userenv = Environment(
        env.app, env.plugin, User(env.user.client, username), None
    )
    for permission in env.app.permissions.values():
        if permission.check(userenv):
            perms.append(permission.name)
    env.msg("%s has following permissions: %s" % (username, ', '.join(perms)))


def listperms(env):
    env.msg(
        "Available permissions: %s" % ', '.join(env.app.permissions.keys())
    )


def activate_plugin(env, plugin):
    if plugin.lower() == 'manage':
        env.msg("Manage plugin is always active")
    elif plugin in env.app.plugins:
        env.app.plugins[plugin].activate()
        env.msg("%s activated" % env.app.plugins[plugin].name)
    else:
        env.msg("Plugin %s not found" % plugin)


def deactivate_plugin(env, plugin):
    if plugin.lower() == 'manage':
        env.msg("Manage plugin cannot be deactivated")
    elif plugin in env.app.plugins:
        env.app.plugins[plugin].deactivate()
        env.msg("%s deactivated" % env.app.plugins[plugin].name)
    else:
        env.msg("Plugin %s not found" % plugin)


def list_plugins(env):
    active_plugins = sorted(
        plugin.name for plugin in env.app.plugins.values() if plugin.active
    )
    inactive_plugins = sorted(
        plugin.name for plugin in env.app.plugins.values() if not plugin.active
    )
    env.msg("Active plugins: %s" % (
        ', '.join(active_plugins)
        if active_plugins
        else 'No active plugins'
    ))
    env.msg("Inactive plugins: %s" % (
        ', '.join(inactive_plugins)
        if inactive_plugins
        else 'No inactive plugins'
    ))


def register(app):
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

    deny_cmd = perms_plugin.add_command(
        'permissions',
        'Show what permissions a user has'
    )
    deny_cmd.add_argument('username')
    deny_cmd.guard(admin)
    deny_cmd.bind(permissions)

    listperms_cmd = perms_plugin.add_command(
        'listperms',
        'Show available permissions'
    )
    listperms_cmd.guard(admin)
    listperms_cmd.bind(listperms)

    help_plugin = app.add_plugin("Help")
    help_cmd = help_plugin.add_command('help', 'Displays help about commands')
    help_cmd.add_argument('command', default=None, nargs='?')
    help_cmd.bind(show_help)

    manage_plugin = app.add_plugin("Manage")
    activate_cmd = manage_plugin.add_command('activate', 'Activate a plugin')
    activate_cmd.add_argument('plugin')
    activate_cmd.guard(admin)
    activate_cmd.bind(activate_plugin)

    deactivate_cmd = manage_plugin.add_command(
        'deactivate', 'Deactivate a plugin'
    )
    deactivate_cmd.add_argument('plugin')
    deactivate_cmd.guard(admin)
    deactivate_cmd.bind(deactivate_plugin)

    plugins_cmd = manage_plugin.add_command('plugins', 'List plugins')
    plugins_cmd.guard(admin)
    plugins_cmd.bind(list_plugins)
