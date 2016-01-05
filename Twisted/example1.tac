# example #1

from twisted.application import internet, service
from twisted.web.server import Site
from twisted.web.static import File

resource = File('/root/Vision/Twisted/html')
factory = Site(resource) # this generates a factory which is really all that's
                        # needed for the rest
application = service.Application('static_serve')   # create an application
staticService = internet.TCPServer(80, factory)     # create the service the
                                                    # the app will use, using
                                                    # a factory
staticService.setServiceParent(application)         # set app to have the service

# call twistd -y example1.tac to start the service as a daemon
# then call kill <number in twistd.pid> to end the process :)
