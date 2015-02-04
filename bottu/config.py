import os
from yaml import loader

DEFAULTS = {
    'redis_dsn': 'redis://127.0.0.1:6379/0'
}
TYPE_MAP = {
    'port': int,
    'name': str,
    'channels': lambda channels: list(map(str, channels))
}


NULL = object()


class SafeEnvLoader(loader.SafeLoader):
    yaml_constructors = {}

    def __init__(self, stream):
        loader.Reader.__init__(self, stream)
        loader.Scanner.__init__(self)
        loader.Parser.__init__(self)
        loader.Composer.__init__(self)
        loader.SafeConstructor.__init__(self)
        loader.Resolver.__init__(self)

    @classmethod
    def load(cls, stream):
        instance = cls(stream)
        try:
            return instance.get_single_data()
        finally:
            instance.dispose()


def constructor(instance, node):
    value = instance.construct_scalar(node)
    return os.environ.get(value, NULL)
SafeEnvLoader.add_constructor('!env', constructor)


def parse_config(stream):
    config = {}
    config.update(DEFAULTS)
    config.update({
        key: value for key, value in SafeEnvLoader.load(stream).items()
        if value is not NULL
    })
    return {
        key: TYPE_MAP.get(key, lambda x: x)(value)
        for key, value in config.items()
    }
