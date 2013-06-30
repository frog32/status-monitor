from widgets.base_widget import BaseWidget


class Widget(BaseWidget):
    name = 'text'

    def initialize(self, client):
        self.message_to_client(client, 'display', {'text': self.config['text']})
