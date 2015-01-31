# -*- coding: utf-8 -*-
from twisted.python import log
import sys

import docopt
import yaml

from bottu.core import Application


__doc__ = '''Bottu.

Usage:
  bottu run <config> [-v] [--redis-dsn=<redis_dsn>]
  bottu grant <username> <permission> <config> [--redis-dsn=<redis_dsn>] [-v]
  bottu revoke <username> <permission> <config> [--redis-dsn=<redis_dsn>] [-v]
  bottu -h | --help

Options:
  -h --help                 Show this screen.
  -v --verbose              Verbose logging.
  --redis-dsn=<redis_dsn>   Redis DSN to use [default: redis://127.0.0.1:6379/0].
'''


def parse_config(args):
    with open(args['<config>']) as fobj:
        config = yaml.load(fobj)
    config['redis_dsn'] = config.get('redis_dsn', args['--redis-dsn'])
    return config


def run():
    options = docopt.docopt(__doc__)
    config = parse_config(options)
    if options['--verbose']:
        log.startLogging(sys.stdout)
    app = Application(**config)
    if options['run']:
        app.run()
    elif options['grant']:
        app.grant_permission(options['<username>'], options['<permission>'])
    elif options['revoke']:
        app.revoke_permission(options['<username>'], options['<permission>'])
