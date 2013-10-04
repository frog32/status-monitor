from twisted.application import service
from twisted.internet import protocol, reactor


class StatusMonitorProtocol(protocol.Protocol):
    def connectionMade(self):
        self.factory.clients.append(self)
        self.factory.widget_manager.init_client(self)

    def connectionLost(self, reason):
        self.factory.clients.remove(self)


class StatusMonitorFactory(protocol.ServerFactory):
    protocol = StatusMonitorProtocol

    def __init__(self, widget_manager):
        self.widget_manager = widget_manager
        self.clients = []


class WidgetManager(service.Service):
    js_include = (
        '//cdnjs.cloudflare.com/ajax/libs/jquery/2.0.2/jquery.min.js',
        '//cdnjs.cloudflare.com/ajax/libs/underscore.js/1.4.4/underscore-min.js',
        '//cdnjs.cloudflare.com/ajax/libs/backbone.js/1.0.0/backbone-min.js',
        '//cdnjs.cloudflare.com/ajax/libs/sockjs-client/0.3.4/sockjs.min.js',
        '//cdnjs.cloudflare.com/ajax/libs/moment.js/2.1.0/moment.min.js',
        '/static/app.js',
    )
    css_include = (
        '/static/app.css',
    )
    template = """<!DOCTYPE html>
<html>
    <head>
    <title>Status Monitor</title>
    %(js)s
    %(css)s
    </head>
    <body>
    %(body)s
    </body>
</html>"""

    def __init__(self, config, aggregator_hub):
        self.last_id = 0
        self.config = config
        self.aggregator_hub = aggregator_hub
        self.sm_factory = StatusMonitorFactory(self)
        self.widgets = []

    def get_id(self):
        self.last_id += 1
        return self.last_id

    def startService(self):
        self.running = 1
        self.root = self.get_widget_instance(*self.config)
        for w in self.widgets:
            # todo: durch service mechanik ersetzen
            reactor.callWhenRunning(w.register_backend)

    def get_widget_instance(self, name, config, *args):
        widget_class = self.load_widget(name)
        instance = widget_class(self, config, *args)
        instance.register(self.aggregator_hub)
        return instance

    def load_widget(self, name):
        mod = __import__('widgets.%s' % (name,), globals(), locals(), ['Widget'], 0)
        return mod.Widget

    def render(self, resrc):
        return self.template % {
            'js': '\n'.join('<script src="%s"></script>' % j for j in self.js_include),
            'css': '\n'.join('<link rel="stylesheet" type="text/css" href="%s">' % c for c in self.css_include),
            'body': self.root.render_base(),
        }

    def init_client(self, client):
        client.transport.write({'target': 'sm', 'type': 'create_root', 'data': {'name': self.root.name, 'id': self.root.id}})
        self.root.initialize(client)

    def message_broadcast(self, message):
        """sends a message to all clients"""
        for client in self.sm_factory.clients:
            client.transport.write(message)
