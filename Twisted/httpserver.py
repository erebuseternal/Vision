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
from httpmessage import *

class Switch(LineReceiver):

    response = None
    request = Request() # we initialize a new request object
                        # there will be only one request per switch

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
                self.createResponse()

    def rawDataReceived(self, data):
        self.request.SetBody(data)
        # we reset the request's parse line
        self.request.ParseLine(None)
        self.createResponse()

    def createResponse(self):
        # now we start writing lines
        line = self.request.WriteLine()
        while line or line == '':
            self.sendLine(line)
            line = self.request.WriteLine()
        # and now we write out the data
        if self.request.has_body:
            self.sendLine(self.request.WriteBody())
        # finally we close the connection
        self.transport.loseConnection()


from twisted.internet.protocol import ServerFactory, Protocol

class Echo(Protocol):

    def dataReceived(self, data):
        self.transport.write()

class MyFactory(ServerFactory):
    def buildProtocol(self, addr):
        return Switch()

from twisted.web.server import Site
from twisted.application import internet, service
from twisted.web.resource import Resource

application = service.Application('test')
staticService = internet.TCPServer(80, MyFactory())
staticService.setServiceParent(application)
