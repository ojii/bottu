# -*- coding: utf-8 -*-
from twisted.python import log
import sys

import docopt

from bottu.config import parse_config
from bottu.core import Application


__doc__ = '''Bottu.

Usage:
  bottu run <config> [-v]
  bottu grant <username> <permission> <config> [-v]
  bottu revoke <username> <permission> <config> [-v]
  bottu -h | --help

Options:
  -h --help                 Show this screen.
  -v --verbose              Verbose logging.
'''


def run():
    options = docopt.docopt(__doc__)
    with open(options['<config>']) as fobj:
        config = parse_config(fobj)
    if options['--verbose']:
        log.startLogging(sys.stdout)
    app = Application(**config)
    if options['run']:
        app.run()
    elif options['grant']:
        app.grant_permission(options['<username>'], options['<permission>'])
    elif options['revoke']:
        app.revoke_permission(options['<username>'], options['<permission>'])
