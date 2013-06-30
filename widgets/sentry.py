import json
import re
import urllib

from twisted.web.client import getPage
from twisted.internet import defer, task
from widgets.base_widget import BaseWidget

CSRF_RE = re.compile(r"name='csrfmiddlewaretoken' value='([A-Za-z0-9]+)'")


class Widget(BaseWidget):
    name = 'sentry'
    base_config = {
        'username': '',
        'password': '',
    }

    def __init__(self, *args, **kwargs):
        super(Widget, self).__init__(*args, **kwargs)
        self.cookies = {}

    def get_widgets(self):
        return [self]

    def render_base(self):
        return '<div id="widget-%s" class="widget"></div>' % self.id

    # def initialize(self, client):

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
        self.task.start(30)

    @defer.inlineCallbacks
    def update(self):
        try:
            data = yield getPage("%sapi/itcrowd/groups/trends/?minutes=1440&limit=5" % self.config['url'], cookies=self.cookies)
        except Exception:
            raise
        data = json.loads(data)
        update = [{'project': e['project']['name'], 'count': e['count']} for e in data]
        self.message_broadcast('update', update)
