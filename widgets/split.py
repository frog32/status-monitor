from widgets.base_widget import BaseWidget


class Widget(BaseWidget):
    name = 'split'
    base_config = {
        'direction': 'vertical',
    }

    def __init__(self, *args, **kwargs):
        super(Widget, self).__init__(*args, **kwargs)
        self.subwidgets = [self.widget_manager.get_widget_instance(*a) for a in self.args]

    def get_widgets(self):
        return [self]

    def render_base(self):
        subwidgets = ''.join(widget.render_base() for widget in self.subwidgets)
        return '<div id="widget-%s" class="widget">%s</div>' % (self.id, subwidgets)

    def initialize(self, client):
        self.message_to_client(client, 'initialize', {'subwidgets': [{'name': s.name, 'id': s.id} for s in self.subwidgets], 'direction': self.config['direction']})
        for s in self.subwidgets:
            s.initialize(client)