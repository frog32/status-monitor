from collections import defaultdict
from copy import copy


class BaseAggregator(object):
    name = ''
    base_config = {}

    def __init__(self, config, *args):
        self.config = copy(self.base_config)
        self.config.update(config)
        self.args = args
        self.listeners = defaultdict(list)

    def register_listener(self, event, listener):
        self.listeners[event].append(listener)

    def unregister_listener(self, event, listener):
        self.listeners[event].remove(listener)

    def call(self, event, *args, **kwargs):
        for listener in self.listeners[event]:
            listener(*args, **kwargs)

