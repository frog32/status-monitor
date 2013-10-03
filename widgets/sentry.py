from widgets.base_widget import BaseWidget


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
        self.last_data = []

    def register(self, aggregator_hub):
        aggregator = aggregator_hub.get('sentry')
        aggregator.register_listener('newData', self.update)

    def initialize(self, client):
        self.message_to_client(client, 'update', self.last_data)

    def update(self, data):
        update = [{
            'project': e['project']['name'],
            'count': e['count'],
            'message': e['message'],
            'level': e['levelName'],
        } for e in data]
        self.message_broadcast('update', update)
        self.last_data = update
