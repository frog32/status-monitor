import json

from twisted.web.client import getPage
from twisted.internet import defer, task
from widgets.base_widget import BaseWidget

from pusher_client.client import connectPusher


class Widget(BaseWidget):
    name = 'travis'
    base_config = {
        'api_url': 'https://api.travis-ci.com/',
    }

    def __init__(self, *args, **kwargs):
        super(Widget, self).__init__(*args, **kwargs)
        self.last_data = []
        self.pusher_key = None
        self.access_token = None
        self.user = {}
        self.pusher_protocol = None
        self.repositorys = {}

    def update_repo(self, repo_data):
        new_repo = {}
        for f in ("id", "slug", "last_build_state", "last_build_finished_at", "last_build_number", "last_build_duration"):
            new_repo[f] = repo_data[f]
        self.repositorys[repo_data["id"]] = new_repo
        self.message_broadcast("update", new_repo)

    def initialize(self, client):
        for repo in self.repositorys.values():
            self.message_to_client(client, 'update', repo)

    @defer.inlineCallbacks
    def api(self, path, method='GET', data={}):
        kwargs = {}
        headers = {'Accept': 'application/json; version=2'}
        if method == 'POST':
            kwargs['postdata'] = json.dumps(data)
            headers['Content-Type'] = 'application/json; charset=utf-8'
        if self.access_token:
            headers['Authorization'] = 'token %s' % self.access_token
        data = yield getPage("%s%s" % (self.config["api_url"], path),
                             method=method,
                             headers=headers,
                             **kwargs)
        obj = json.loads(data)
        defer.returnValue(obj)

    def on_repo_event(self, event, channel, data):
        print data
        self.update_repo(data["repository"])

    def on_user_event(self, event, channel, data):
        print "user event", event, channel, data


    @defer.inlineCallbacks
    def register_backend(self):
        # get config from travis
        try:
            data = yield self.api("config")
        except Exception:
            raise
        self.pusher_key = data["config"]["pusher"]["key"]

        # authenticate travis
        try:
            data = yield self.api("auth/github",
                                  method='POST',
                                  data={
                                      'github_token': self.config['token'],
                                  })
        except Exception:
            raise
        self.access_token = data["access_token"]

        # get user info
        try:
            data = yield self.api("users")
        except Exception:
            raise
        self.user = data["user"]

        # get repos
        try:
            data = yield self.api(str("repos?member=%s" % self.user["login"]))
        except Exception:
            print "fehler beim laden der repos"
            raise
        for repo in data["repos"]:
            self.update_repo(repo)

        # connect pusher
        print self.pusher_key
        try:
            self.pusher_protocol = yield connectPusher(self.pusher_key, debug=True)
        except Exception:
            print 'boeser fehler'
            raise

        # get channel auth
        try:
            data = yield self.api("pusher/auth",
                                  method="POST",
                                  data={"socket_id": self.pusher_protocol.socket_id,
                                        "channels": ["private-%s" % c for c in self.user["channels"]]
                                        })
        except Exception:
            raise
        channels = data["channels"]
        for channel_name, auth in channels.items():
            print "subscribe to %s" % channel_name
            channel = self.pusher_protocol.subscribe(channel_name, auth=auth)
            if channel.name.startswith("private-user-"):
                channel.addObserver(None, self.on_user_event)
            else:
                channel.addObserver("build:", self.on_repo_event, False)
        print "finished subscribing"
