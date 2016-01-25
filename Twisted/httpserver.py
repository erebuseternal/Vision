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
from copy import deepcopy
import re

"""
A server resource must have a CreateResponse method which takes a request
and returns a response object. The server switches will call CreateResponse
on the Resource that matches the url found in the request. Just look at the
Switch Class.
"""

# this is the base class, and it just echos the request object
# it should also have a path attribute, which specifies the path
# it is set to be a resource under
class ServerResource:

    path = '/'

    def SetPath(self, path):
        checkType(path, str)
        self.path = path

    def CreateResponse(self, request):
        # this request will be a request object
        # this method needs to deal with this request object and return
        # a response. I am going to make this basic class just echo
        response = Response()
        response.version = request.version
        response.status = Status(200)
        response.headers = request.headers
        response.header_names = request.header_names
        response.has_body = request.has_body
        response.body = request.body
        return response

# this is a resource that serves
class Directory(ServerResource):

    def __init__(self, directory):
        # directory is the directory from which it will serve things in the
        # request
        if directory[-1] != '/':
            directory = directory + '/'
        self.directory = directory

    def CreateResponse(self, request):
        # first we find the part of the url after the path this resource
        # was set under
        re_expression = re.compile(self.path)
        match = re.search(re_expression, request.url.path)
        index_of_rest = match.end()
        path = request.url.path[index_of_rest:]
        try:
            file = open(self.directory + path, 'r')
        except:
            # in this case we need to send a 404
            response = Response()
            response.SetVersion(Version(1.1))
            response.SetStatus(Status(404))
            response.SetBody('<p>404 Not Found<p>')
            return response
        # okay so we got the file, so now to send it
        body = file.read()
        response = Response()
        response.SetVersion(Version(1.1))
        response.SetStatus(Status(200))
        response.SetBody(body)  # set body adds the appropriate headers for us
        return response


class Switch(LineReceiver):

    def __init__(self, factory):
        self.factory = factory
        self.response = None
        self.request = Request() # we initialize a new request object
                            # there will be only one request per switch

    def end(self, input):
        self.transport.loseConnection()

    def startResource(self):
        # this method finds the best resource given the path in the url of the
        # request. If nothing is found it returns a 404 Not Found response
        # if something is found it creates a defer by defering to a thread
        # and adds as a callback sendResponse which takes the response object
        # that is returned
        path = self.request.url.path
        resource = self.factory.getResource(path)
        if not resource:
            # we send back a 404 not found method
            response = Response()
            response.SetVersion(Version(1.1))
            response.SetStatus(Status(404))
            response.SetBody('<p>404 %s</p>' % Status(404).message)
            self.sendResponse(response)
            return
        # we now know that we have a resource class instance so now we will create
        # a defered where it is instantiated and then CreateResponse is called
        # passing in the request
        # by defering to a thread, we can allow our resource to call expensive
        # resources without having to worry about the rest of the server
        defered = threads.deferToThread(resource.CreateResponse, self.request)
        # the returned response will be send here
        defered.addCallbacks(self.sendResponse, self.sendServerError)

    def sendServerError(self, failure):
        # this method is called if an error is thrown by a resource's CreateResponse
        # it will send a server error response
        response = Response()
        response.SetVersion(Version(1.1))
        response.SetStatus(Status(500))
        response.SetBody('<p>500 %s</p>' % Status(500).message)
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
        # first we check that resource is a ServerResource
        if not isinstance(resource, ServerResource):
            raise Issue('Input Resource %s is Not a Subclass of ServerResource' % resource)
        # then we make sure the path is a string
        checkType(path, str)
        # first we set the path on the resource
        resource.SetPath(path)
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
        if path in self.resources: # this is just to check we did find something, it is possible we didn't
            # then we return a copy of the resource. This keeps our server stateless
            return deepcopy(self.resources[current_best_match])
        else:
            return None # we didn't find anything

    def buildProtocol(self, addr):
        return Switch(self)
