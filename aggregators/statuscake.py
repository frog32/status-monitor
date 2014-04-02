import json

from twisted.web.client import getPage
from twisted.internet import defer, task

from aggregators.base_aggregator import BaseAggregator


class Aggregator(BaseAggregator):
    name = 'statuscake'
    base_config = {
        'token': '',
        'username': '',
        'update_rate': 60,
        'api_url': "https://www.statuscake.com/API/",
    }

    def __init__(self, *args, **kwargs):
        super(Aggregator, self).__init__(*args, **kwargs)
        self.last_data = {}
        self.down_hosts = []

    def start(self):
        self.task = task.LoopingCall(self.update)
        self.task.start(self.config["update_rate"])

    @defer.inlineCallbacks
    def api(self, path, method='GET', data={}):
        headers = {
            "API": self.config["token"],
            "Username": self.config["username"],
        }
        data = yield getPage("%s%s" % (self.config["api_url"], path),
                             method=method,
                             headers=headers)
        obj = json.loads(data)
        defer.returnValue(obj)

    @defer.inlineCallbacks
    def update(self):
        try:
            tests = yield self.api("Tests/")
        except Exception as e:
            print e
            return

        update = {
            "tests_total": len(tests),
            "tests_down": len(filter(lambda x: x["Status"] == "Down", tests)),
            "tests_up": len(filter(lambda x: x["Status"] == "Up", tests)),
            "uptime": sum(map(lambda x: x["Uptime"], tests)) / float(len(tests)),
        }
        if update != self.last_data:
            self.call('update', update)
            self.last_data

        # check down hosts
        newly_down = filter(lambda x: x["Status"] == "Down", tests)
        for down in newly_down:
            if not down in self.down_hosts:
                self.call('down', down)
                self.down_hosts.append(down)
        for already_down in self.down_hosts:
            if already_down not in newly_down:
                self.call('up', already_down)
                self.down_hosts.remove(already_down)
