import json
import re

from twisted.web.client import getPage
from twisted.internet import defer, task
from widgets.base_widget import BaseWidget

CSRF_RE = re.compile(r"name='csrfmiddlewaretoken' value='([A-Za-z0-9]+)'")


class Widget(BaseWidget):
    name = 'github'
    base_config = {
        'token': '',
        'company': '',
        'update_rate': 5 * 60,
        'api_url': "https://api.github.com/",
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
        kwargs = {}
        headers = {
            "Accept": "application/json",
            "Authorization": "token %s" % self.config["token"],
        }
        if method == 'POST':
            kwargs["postdata"] = json.dumps(data)
            headers["Content-Type"] = "application/json; charset=utf-8"
        data = yield getPage("%s%s" % (self.config["api_url"], path),
                             method=method,
                             headers=headers,
                             **kwargs)
        obj = json.loads(data)
        defer.returnValue(obj)

    @defer.inlineCallbacks
    def update(self):
        try:
            data = yield self.api("orgs/%s" % self.config["company"])
        except Exception as e:
            print e
            return
        update = {
            "private_repos": data["owned_private_repos"],
            "public_repos": data["public_repos"]
        }
        self.message_broadcast('update', update)
        self.last_data = update
