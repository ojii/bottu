# -*- coding: utf-8 -*-
from argparse import ArgumentParser
from twisted.python import log
import sys
from bottu.core import Application
import yaml


def parse_config(args):
    with open(args.config) as fobj:
        config = yaml.load(fobj)
    config['redis_dsn'] = config.get('redis_dsn', args.redis_dsn)
    return config


def run():
    parser = ArgumentParser()
    parser.add_argument('config')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', default=False)
    parser.add_argument('--redis-dsn', dest='redis_dsn', default='redis://127.0.0.1:6379/0')
    args = parser.parse_args()
    config = parse_config(args)
    if args.verbose:
        log.startLogging(sys.stdout)
    app = Application(**config)
    app.run()
