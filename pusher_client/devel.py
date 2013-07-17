from twisted.internet import reactor

from client import connectPusher


def test_fn(event, channel, data):
    print event, channel, data


def connected(p):
    print p
    channel = p.subscribe('common')
    channel.addObserver('job:', test_fn, False)

d = connectPusher('5df8ac576dcccf4fd076', use_ssl=False, debug=True)
d.addCallback(connected)
reactor.run()
