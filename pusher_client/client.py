import json

from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.internet.endpoints import TCP4ClientEndpoint, SSL4ClientEndpoint
from autobahn.websocket import WebSocketClientFactory, WebSocketClientProtocol


class Channel(object):
    def __init__(self, name):
        self.name = name
        self.subscribed = False
        self.observers = []

    def onMessage(self, event, data):
        self.dispatch(data, event)

    def addObserver(self, event, observerfn, exact=True):
        self.observers.append((event, observerfn, exact))

    def dispatch(self, data, event):
        for e, fn, exact in self.observers:
            if event == e or e is None or (not exact and event.startswith(e)):
                fn(event, self.name, data)


class PusherClientProtocol(WebSocketClientProtocol):

    def __init__(self, debug=False):
        self.debug = debug
        self.connected = False
        self.channels = {}
        self.socket_id = None
        self.pusherConnectionEstablishedDeferred = Deferred()

    def onConnect(self, connectionResponse):
        self.connected = True
        print "onConnect"

    def onMessage(self, payload, binary):
        if binary:
            raise Exception("binary message received")
        packet = json.loads(payload)

        if self.debug:
            print packet

        event = packet["event"]
        data = json.loads(packet["data"])
        if event == "pusher:connection_established":
            self.onPusherConnectionEstablished(data["socket_id"])
        elif event == "pusher:error":
            self.onPusherError(data["code"], data["message"])
        elif not "channel" in packet:
            raise Exception("missing a channel")
        elif packet["channel"] not in self.channels:
            raise Exception("got a message from an unknown channel")
        else:
            self.channels[packet["channel"]].onMessage(event, data)

    def sendMessage(self, payload):
        WebSocketClientProtocol.sendMessage(self, json.dumps(payload))

    # events pusher -> client
    def onPusherConnectionEstablished(self, socket_id):
        self.socket_id = socket_id
        self.pusherConnectionEstablishedDeferred.callback(self)

    def onPusherError(self, code, message):
        print "pusher:error", code, message

    # events client -> pusher
    def subscribe(self, channel, auth=None, channel_data=None):
        message = {
            "event": "pusher:subscribe",
            "data": {
                "channel": channel,
            }
        }
        if auth:
            message["data"]["auth"] = auth
        if channel_data:
            message["data"]["channel_data"] = channel_data
        self.sendMessage(message)
        new_channel = Channel(name=channel)
        self.channels[channel] = new_channel
        return new_channel

    def unsubscribe(self, channel):
        if not channel in self.channels:
            raise Exception("Not subscribed to this channel")
        message = {
            "event": "pusher:unsubscribe",
            "data": {
                "channel": channel,
            }
        }
        self.sendMessage(message)
        del self.channels['channel']


class PusherClientFactory(WebSocketClientFactory):
    protocol = PusherClientProtocol

    def __init__(self, api_key, use_ssl=True, debug=False, **kwargs):
        self.debug = debug
        client_name = 'js'
        client_version = '2.0.4'
        proto = use_ssl and 'wss' or 'ws'
        port = use_ssl and 443 or 80
        url = '%s://ws.pusherapp.com:%s/app/%s?client=%s&version=%s&protocol=6&flash=false' % (proto, port, api_key, client_name, client_version)
        WebSocketClientFactory.__init__(self, url=url, **kwargs)

    def clientConnectionFailed(self, connector, reason):
        print 'connection failed', connector, reason

    def clientConnectionLost(self, connector, reason):
        print 'connection lost', connector, reason

    def buildProtocol(self, addr):
        p = self.protocol(debug=self.debug)
        p.factory = self
        return p


def connectPusher(api_key, use_ssl=True, timeout=30, bindAddress=None, debug=False):
    d1 = Deferred()
    pcf = PusherClientFactory(api_key, use_ssl=use_ssl, debug=debug)
    if pcf.isSecure:
        # create default client SSL context factory when none given
        from twisted.internet import ssl
        contextFactory = ssl.ClientContextFactory()
        point = SSL4ClientEndpoint(reactor, pcf.host, pcf.port, contextFactory, timeout, bindAddress)
    else:
        point = TCP4ClientEndpoint(reactor, pcf.host, pcf.port, timeout, bindAddress)

    d2 = point.connect(pcf)

    def got_protocol(p):
        p.pusherConnectionEstablishedDeferred.chainDeferred(d1)
        return p

    d2.addCallbacks(got_protocol, d1.errback)
    return d1
