from twisted.application import internet, service
from httpserver import *
application = service.Application('http')
factory = SwitchFactory()
factory.RegisterResource(ServerResource, '/')
staticService = internet.TCPServer(8000, factory)
staticService.setServiceParent(application)
