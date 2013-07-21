import json
import re
import urllib

from twisted.web.client import getPage
from twisted.internet import defer, task
from twisted.python.failure import Failure
from widgets.base_widget import BaseWidget

CSRF_RE = re.compile(r"name='csrfmiddlewaretoken' value='([A-Za-z0-9]+)'")


class Widget(BaseWidget):
    name = 'statuscake'
    base_config = {
        'token': '',
        'username': '',
        'update_rate': 60,
        'api_url': "https://www.statuscake.com/API/",
    }

    def __init__(self, *args, **kwargs):
        super(Widget, self).__init__(*args, **kwargs)
        self.last_data = {}

    def initialize(self, client):
        self.message_to_client(client, 'update', self.last_data)

    def register_backend(self):

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
            "uptime": sum(map(lambda x: x["Uptime"], tests)),
            "failures": filter(lambda x: x["Status"] == "Down", tests),
        }
        self.message_broadcast('update', update)
        self.last_data = update
