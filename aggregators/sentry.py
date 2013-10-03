import json
import re
import urllib

from twisted.internet import defer, task, error
from twisted.web.error import Error as TwistedWebError
from twisted.python import log
from twisted.web.client import getPage

from aggregators.base_aggregator import BaseAggregator

CSRF_RE = re.compile(r"name='csrfmiddlewaretoken' value='([A-Za-z0-9]+)'")


class Aggregator(BaseAggregator):
    name = 'sentry'
    base_config = {
        'username': '',
        'password': '',
        'count': 20,
        'update_rate': 60,
    }

    def __init__(self, *args, **kwargs):
        super(Aggregator, self).__init__(*args, **kwargs)
        self.cookies = {}
        self.last_data = []

    @defer.inlineCallbacks
    def start(self):
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
        self.call('newData', data)
