from widgets.base_widget import BaseWidget


class Widget(BaseWidget):
    name = 'statuscake'
    base_config = {
        'token': '',
        'username': '',
        'update_rate': 60,
        'api_url': "https://www.statuscake.com/API/",
    }

    def __init__(self, *args, **kwargs):
        super(Widget, self).__init__(*args, **kwargs)
        self.last_data = {'failures': []}

    def register(self, aggregator_hub):
        aggregator = aggregator_hub.get('statuscake')
        aggregator.register_listener('update', self.update_numbers)

    def initialize(self, client):
        self.message_to_client(client, 'update', self.last_data)

    def update_numbers(self, update):
        self.message_broadcast('update', update)
        self.last_data.update(update)

    def on_host_goes_down(self, host):
        self.last_data['failures'].append(host)
        self.message_broadcast('goes_down', host)

    def on_host_comes_up(self, host):
        self.last_data['failures'].remove(host)
        self.message_broadcast('comes_up', host)
