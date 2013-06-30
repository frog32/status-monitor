from twisted.application import internet, service

from server import site, widget_manager

application = service.Application("status-monitor")


i = internet.TCPServer(8000, site)
i.setServiceParent(application)

widget_manager.setServiceParent(application)
