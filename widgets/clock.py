from datetime import datetime
from twisted.internet import task
from widgets.base_widget import BaseWidget


class Widget(BaseWidget):
    name = 'clock'

    def register_backend(self):
        self.task = task.LoopingCall(self.update)
        self.task.start(1)

    def update(self):
        self.message_broadcast('update', {'time': datetime.now().strftime("%H:%M:%S")})
