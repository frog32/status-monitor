import json

from twisted.web.client import getPage
from twisted.internet import defer, task
from aggregators.base_aggregator import BaseAggregator


class Aggregator(BaseAggregator):
    name = 'github'
    base_config = {
        'token': '',
        'company': '',
        'update_rate': 5 * 60,
        'api_url': "https://api.github.com/",
    }

    def __init__(self, *args, **kwargs):
        super(Aggregator, self).__init__(*args, **kwargs)
        self.last_data = {}

    def start(self):
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
        # company info
        if 'updateCompanyInfo' in self.listeners or not 'company_info' in self.last_data:
            try:
                data = yield self.api("orgs/%s" % self.config["company"])
            except Exception as e:
                print e
                return
            update = {
                "private_repos": data["owned_private_repos"],
                "public_repos": data["public_repos"]
            }
            if(update != self.last_data.get('company_info', None)):
                self.call('updateCompanyInfo', update)
                self.last_data['company_info'] = update
