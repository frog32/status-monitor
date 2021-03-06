from copy import copy


class BaseWidget(object):
    name = ''
    base_config = {}

    def __init__(self, widget_manager, config, *args):
        self.widget_manager = widget_manager
        self.id = widget_manager.get_id()
        self.config = copy(self.base_config)
        self.config.update(config)
        self.args = args
        widget_manager.widgets.append(self)

    def initialize(self, client):
        """initialize this widget on a new client"""

    def register(self, aggregator_hub):
        """register all needed callbacks on aggregators"""

    def message_to_client(self, client, message_type, data):
        message = {'target': self.id, 'type': message_type, 'data': data}
        client.transport.write(message)

    def message_broadcast(self, message_type, data):
        """sends a message to this widget on all clients"""
        message = {'target': self.id, 'type': message_type, 'data': data}
        self.widget_manager.message_broadcast(message)

    def register_backend(self):
        pass

    def render_base(self):
        return '<div class="widget %s" id="widget-%s"></div>' % (self.name, self.id)
