# example 2

from twisted.application import internet, service
from twisted.web.server import Site
from twisted.web.static import File

root = File('/root/Vision/Twisted/html')
root.putChild('apache', File('/var/www/html'))  # the new stuff here
factory = Site(root)
application = service.Application('static2')
staticService = internet.TCPServer(80, factory)
staticService.setServiceParent(application)
