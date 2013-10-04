from datetime import datetime
from twisted.internet import task
from widgets.base_widget import BaseWidget

import usb

REQUEST_TYPE_SEND = usb.util.build_request_type(usb.util.CTRL_OUT,
                                                usb.util.CTRL_TYPE_CLASS,
                                                usb.util.CTRL_RECIPIENT_DEVICE)

USBRQ_HID_SET_REPORT = 0x09
USB_HID_REPORT_TYPE_FEATURE = 0x03


class Widget(BaseWidget):
    name = 'clock'
    def __init__(self, *args, **kwargs):
        super(Widget, self).__init__(*args, **kwargs)
        self.device = usb.core.find(idVendor=0x16c0,
                                    idProduct=0x05df)
        self.on = False

    def register_backend(self):
        self.task = task.LoopingCall(self.update)
        self.task.start(1)

    def update(self):
        self.message_broadcast('update', {'time': datetime.now().strftime("%H:%M:%S")})
        self.write_device(ord("s"))
        if self.on:
            self.write_device(255)
            self.on = False
        else:
            self.write_device(0)
            self.on = True
        self.write_device(0)
        self.write_device(0)

    def write_device(self, byte):
        self.device.ctrl_transfer(REQUEST_TYPE_SEND, USBRQ_HID_SET_REPORT,
                                        (USB_HID_REPORT_TYPE_FEATURE << 8) | 0,
                                         byte,
                                         [])