import os

import yaml

DEFAULTS = {
    'redis_dsn': 'redis://127.0.0.1:6379/0'
}


NULL = object()


def constructor(instance, node):
    value = instance.construct_scalar(node)
    return os.environ.get(value, NULL)
yaml.add_constructor('!env', constructor)


def parse_config(stream):
    config = {}
    config.update(DEFAULTS)
    config.update({
        key: value for key, value in yaml.load(stream).items()
        if value is not NULL
    })
    return config
