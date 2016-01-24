# Python File httpserver.py

"""
This contains the protocol and factory for our resource based http server.
The idea is this. You register resource adress tuples with your server factory.
resources take in a request object and spit out a response object. The server
protocol is then created for each connection, creates a request object (catching
a server error if there is one), and then finds the closest resource to the requested
one in the request, and sends it to that resource by calling the resource.
It then receives the resource and pumps that back out into the network.
Simple as that.
"""

"""
We start with our protocol, called a Switch
"""

from twisted.protocols.basic import LineReceiver
from twisted.internet import threads
from httpmessage import *

class ServerResource:

    def CreateResponse(self, request):
        # this request will be a request object
        # this method needs to deal with this request object and return
        # a response. I am going to make this basic class just echo
        response = Response()
        response.version = request.version
        response.status = Status(200)
        print(response.status)
        response.headers = request.headers
        response.header_names = request.header_names
        response.has_body = request.has_body
        response.body = request.body
        return response

class Switch(LineReceiver):

    response = None
    request = Request() # we initialize a new request object
                        # there will be only one request per switch

    def __init__(self, factory):
        self.factory = factory

    def end(self, input):
        self.transport.loseConnection()

    def startResource(self):
        # this method finds the best resource given the path in the url of the
        # request. If nothing is found it returns a 404 Not Found response
        # if something is found it creates a defer by defering to a thread
        # and adds as a callback sendResponse which takes the response object
        # that is returned
        path = self.request.url.path
        resource_class = self.factory.getResource(path)
        if not resource_class:
            # we send back a 404 not found method
            response = Response()
            response.version = Version(1.1)
            response.status = Status(404)
            self.sendResponse(response)
            return
        # we now know that we have a resource class instance so now we will create
        # a defered where it is instantiated and then CreateResponse is called
        # passing in the request
        # by defering to a thread, we can allow our resource to call expensive
        # resources without having to worry about the rest of the server
        defered = threads.deferToThread(resource_class().CreateResponse, self.request)
        # the returned response will be send here
        defered.addCallbacks(self.sendResponse, self.sendServerError)

    def connectionMade(self):
        # for whatever reason sendLine is not recognized in sendResponse unless
        # a line is written in one of the methods triggered by events.
        # for some wacky reason if I write here through the transport it shows
        # up, if I use sendLine though, it doesn't show up... So this wack-job
        # fix actually works. Don't like it though. Will try to find a way around
        # it in the future
        self.sendLine('a')

    def sendServerError(self, failure):
        # this method is called if an error is thrown by a resource's CreateResponse
        # it will send a server error response
        response = Response()
        response.version = Version(1.1)
        response.status = Status(500)
        self.sendResponse(response)

    def sendResponse(self, response):
        # check that this is a Response
        try:
            checkType(response, Response)
        except:
            # we send a server error response (we have to input None because
            # there is an input for a failure due to this method also being
            # used as a errback)
            self.sendServerError(None)
            return
        # first we send the line parts of the response
        line = response.WriteLine()
        while line or line == '':
            self.sendLine(line)
            line = response.WriteLine()
        # now we see if there is a body
        if response.has_body:
            # we write out the body
            self.transport.write(response.body)
        # now we are done and can loose the connection
        self.transport.loseConnection()



    """
    So line will be top line, headers, and then the gap before a potential
    body which will come in as ''. Once that is done, we have to look
    into the headers to see if there is a body (httpmessage does that for us)
    and if there is we must go into raw mode and receive the rest of the
    data from rawDataReceived in order to grab the body. Then we reset
    the parser and create the response. Create response should close the
    connection for us
    """
    def lineReceived(self, line):
        # this will just make calls to self.request.ParseLine(line)
        # and once it sees line is None and
        self.request.ParseLine(line)
        if self.request.position == 'BODY':
            # once we get to the body we need to check if there is a BODY
            if self.request.has_body:
                # we go into raw mode to grab the body (body doesn't come through
                # lines)
                self.setRawMode()
            else:
                # we reset the request's parse line
                self.request.ParseLine(None)
                self.startResource()

    def rawDataReceived(self, data):
        self.request.SetBody(data)
        # we reset the request's parse line
        self.request.ParseLine(None)
        self.startResource()



from twisted.internet.protocol import ServerFactory, Protocol


class SwitchFactory(ServerFactory):

    resources = {}

    def RegisterResource(self, resource, path):
        # first we check that resource is a subclass of Resource
        if not issubclass(resource, ServerResource):
            raise Issue('Input Resource %s is Not a Subclass of ServerResource' % resource)
        # then we make sure the path is a string
        checkType(path, str)
        # now we register the resource under the path
        self.resources[path] = resource

    # we put this method here, because resources have to do with the factory
    def getResource(self, input_path):
        # this method returns the resource registered under the path that is
        # closest to the input_path, it returns that resource class
        # if nothing is found it returns none
        current_best_match = ''
        for path in self.resources:
            # if the url specifies a file or directory under the resource url
            # and if the resource_url which has been found is longer (and there
            #-fore more specific) than the last one, we save it as current best
            # match
            if path in input_path and len(path) > len(current_best_match):
                current_best_match = path
        if path in self.resources:
            # this is just to check we did find something, it is possible we didn't
            return self.resources[current_best_match]
        else:
            return None # we didn't find anything

    def buildProtocol(self, addr):
        return Switch(self)
"""
from twisted.internet import reactor
from twisted.web.server import Site
from twisted.application import internet, service
from twisted.web.resource import Resource


if __name__ == '__main__':
    factory = SwitchFactory()
    factory.RegisterResource(ServerResource, '/')
    reactor.listenTCP(101, factory)
    reactor.run()

from twisted.application import internet, service
application = service.Application('test')
staticService = internet.TCPServer(80, factory)
staticService.setServiceParent(application)
"""
