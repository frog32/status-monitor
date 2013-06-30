import os
from twisted.web import static, server
from twisted.web.resource import Resource
from txsockjs.factory import SockJSResource

from widget_manager import WidgetManager
from config import MONITOR

widget_manager = WidgetManager(MONITOR)

static_path = os.path.join(os.path.dirname(__file__), 'static')

root = Resource()
root.putChild('static', static.File(static_path))
root.putChild('', widget_manager)
root.putChild("ws", SockJSResource(widget_manager.sm_factory))
site = server.Site(root)
