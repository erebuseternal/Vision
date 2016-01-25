from twisted.internet import reactor
from httpserver import *

if __name__ == '__main__':
    factory = SwitchFactory()
    factory.RegisterResource(Directory('/root/Vision/Twisted/html/'), '/')
    reactor.listenTCP(89, factory)
    reactor.run()
