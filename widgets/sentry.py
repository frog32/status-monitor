import json
import re
import urllib

from twisted.internet import defer, task, error
from twisted.web.error import Error as TwistedWebError
from twisted.python import log
from twisted.web.client import getPage

from widgets.base_widget import BaseWidget

CSRF_RE = re.compile(r"name='csrfmiddlewaretoken' value='([A-Za-z0-9]+)'")


class Widget(BaseWidget):
    name = 'sentry'
    base_config = {
        'username': '',
        'password': '',
        'count': 5,
        'update_rate': 60,
    }

    def __init__(self, *args, **kwargs):
        super(Widget, self).__init__(*args, **kwargs)
        self.cookies = {}
        self.last_data = []

    def initialize(self, client):
        self.message_to_client(client, 'update', self.last_data)

    @defer.inlineCallbacks
    def register_backend(self):
        try:
            data = yield getPage("%slogin/" % self.config['url'], cookies=self.cookies)
        except Exception:
            raise

        result = CSRF_RE.search(data)
        if not result:
            print "error"
            return
        token = result.group(1)

        # login
        try:
            data = yield getPage("%slogin/" % self.config['url'],
                                 method='POST',
                                 postdata=urllib.urlencode({
                                     'csrfmiddlewaretoken': token,
                                     'username': self.config['username'],
                                     'password': self.config['password'],
                                 }),
                                 cookies=self.cookies,
                                 headers={'Content-Type': 'application/x-www-form-urlencoded'})
        except Exception:
            raise

        self.task = task.LoopingCall(self.update)
        self.task.start(self.config["update_rate"])

    @defer.inlineCallbacks
    def update(self):
        try:
            data = yield getPage("%sapi/itcrowd/groups/trends/?minutes=1440&limit=%s" % (self.config['url'], self.config['count']), cookies=self.cookies)
        except error.TimeoutError:
            log.msg("SentryWidget: connection timeout")
            return
        except TwistedWebError:
            return
        data = json.loads(data)
        update = [{
            'project': e['project']['name'],
            'count': e['count'],
            'message': e['message'],
            'level': e['levelName'],
        } for e in data]
        self.message_broadcast('update', update)
        self.last_data = update
