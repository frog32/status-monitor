from twisted.application import service
from twisted.internet import reactor


class AggregatorHub(service.Service):
    def __init__(self, config):
        self.last_id = 0
        self.aggregators = []
        for name, conf in config:
            self.aggregators.append(self.load_aggregator(name)(conf))

    def startService(self):
        self.running = 1
        for a in self.aggregators:
            # todo: durch service mechanik ersetzen
            reactor.callWhenRunning(a.start)

    def get(self, name):
        for a in self.aggregators:
            if a.name == name:
                return a

    def load_aggregator(self, name):
        mod = __import__('aggregators.%s' % (name,), globals(), locals(), ['Aggregator'], 0)
        return mod.Aggregator
