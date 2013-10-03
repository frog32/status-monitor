from twisted.internet import task
from widgets.base_widget import BaseWidget


class Widget(BaseWidget):
    name = 'github'

    def __init__(self, *args, **kwargs):
        super(Widget, self).__init__(*args, **kwargs)
        self.last_data = {}

    def register(self, aggregator_hub):
        aggregator = aggregator_hub.get('github')
        aggregator.register_listener('updateCompanyInfo', self.update_company_info)

    def update_company_info(self, update):
        self.message_broadcast('update', update)
        self.last_data = update

    def initialize(self, client):
        self.message_to_client(client, 'update', self.last_data)
