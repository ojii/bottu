from functools import update_wrapper


class Queued(object):
    def __init__(self):
        self._queue = []
        self._ready = False

    def __call__(self, func):
        def deco(*args, **kwargs):
            if self._ready:
                func(*args, **kwargs)
            else:
                self._queue.append((func, args, kwargs))
        update_wrapper(deco, func)
        deco.ready = self.ready
        return deco

    def ready(self):
        self._ready = True
        while self._queue:
            func, args, kwargs = self._queue.pop(0)
            func(*args, **kwargs)


class CaseInsensitiveDict(dict):
    def __setitem__(self, key, value):
        super(CaseInsensitiveDict, self).__setitem__(key.lower(), value)

    def __getitem__(self, key):
        return super(CaseInsensitiveDict, self).__getitem__(key.lower())

    def __contains__(self, key):
        return super(CaseInsensitiveDict, self).__contains__(key.lower())
