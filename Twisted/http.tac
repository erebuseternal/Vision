from twisted.application import internet, service
from httpserver import *
application = service.Application('http')
factory = SwitchFactory()
factory.RegisterResource(Directory('/root/Vision/Twisted/html/'), '/')
staticService = internet.TCPServer(8000, factory)
staticService.setServiceParent(application)
