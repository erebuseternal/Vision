# Python File isaac.py

"""
The following is an HTTPServer Protocol. It works in the following way:
It will receive a message and parse its lines into method, url, headers,
body, etc. Then you will have registered resources with it. It finds the
best match (and send an error if there isn't one) and then creates a
request object containing all the request info (you can create a class
that also has processing code which will be called before it gets passed
to a call_GET or call_POST method) and passes it to call_GET or call_POST
depending on the method found. If the method is neither get or post, it sends
an error message (saying bad message). call_METHOD should return a response
object, and this response object is used to create the message that gets
send back to the client.

To register a resource use the AddResource method on the protocol.
"""

from twisted.protocols import basic
from twisted.internet import protcol, reactor
import re

"""
The next class represents a request resource. It will be passed to resources
used by a server so that they can access headers, url and body of the message.

It will be passed the url, header dictionary, and body list on initiation. It
then can encapsulate any processing and representation of those elements.
You can choose how you want to make them accessible, etc. But this just means
we have a consistent way of inputting information into one simple object to
pass onto a resource.

All the processing has to happen in process as that is the only thing
that will be called
"""

class Request:

    def __init__(self, url, headers, body):
        self.url = url
        self.headers = headers
        self.body = body

    def Process(self):
        # where all the processing happens
        pass

"""
This is a response object. Create and modify the object in your resources,
but it must have the headers as a dictionary, status as a number, message
as a string, and body as a string: all accessibly as below
"""

class Response:
    # value corresponding to a header should be a list (even if it only has
    # one value)

    headers = {}
    status = None
    message = None
    body = ''


class HTTPServer(basic.lineReceiver):
    method = None
    url = None
    headers = {}
    body = ''
    resources = {}

    def __init__(self, request_object, POST_request_object=None):
        self.lines = []
        self.request_line_expression = re.compile('(?i)([\S]{1,})[\s]{1,}([\S]{1,})[\s]{1,}HTTP\/([\S]{1,})')
        self.header_line_expression = re.compile('([\S]{1,})[\s]*:[\s]*([\s\S]*[\S])')
        self.line_parser = self.request_lineParser
        self.parsed_request_line = False
        self.GET_request_object = request_object
        if POST_request_object:
            self.POST_request_object = POST_request_object
        else:
            self.POST_request_object = request_object

    def lineReceived(self, line):
        self.lines.append(line)
        # if we hit a blank line we know we are going to move onto the body next
        if line.strip() == '':
            self.line_parser = self.body_lineParser
            return
        # parse the line
        self.line_parser(line)
        # if this next evaluates to true, then we just parsed the first line
        # so we need to move onto headers
        if not self.parsed_request_line:
            self.line_parser = self.header_lineParser
            self.parsed_request_line = True
        # we've come to the end. Time to reset and call the method to create
        # and send the response
        if not line:
            # we need to remove the last new-line off of the body
            self.body = self.body[:-1]
            self.parsed_request_line = False
            self.line_parser = self.request_lineParser
            response = self.createResponse()
            self.sendResponse(response)

    def request_lineParser(self, line):
        # this parses the first line in an HTTP response
        line = line.strip()
        match = re.search(self.request_line_expression, line)
        if match:
            self.method = match.group(1).upper()
            self.url = match.group(2)
            self.version = match.group(3)

    def header_lineParser(self, line):
        # we assume header lines have the form: given in the regular
        # expression given in __init__
        # the result (if there is a match) is an additional key value
        # pair in headers. where the key is the header name, and the
        # value is a list of all the attributes found on the other
        # side of the colon
        line = line.strip()
        match = re.search(self.header_line_expression, line):
        if match:
            header = match.group(1)
            values = match.group(2)
            # we value by comma
            values = values.split(',')
            cleaned_values = []
            for value in values:
                cleaned_values.append(value.strip())
            self.headers[header] = cleaned_values

    def body_lineParser(self, line):
        # this just adds an element to the body list
        self.body = self.body + line + '\n'

    def AddResource(self, url, resource):
        # this will add a resource under the specified url. If a url comes into
        # the server and the above url is the best match (i.e. it is the most
        # specific upper directory to be found) then this resource's call_GET
        # or call_POST method will be invoked with a request object initialized
        # and passed into it with request info.
        self.resources[url] = resource

    def findBestMatch(self, url):
        # this finds the best matching url in resources
        # I'm gonna make this stupid simple right now, will make this better later
        current_best_match = ''
        for resource_url in self.resources:
            # if the url specifies a file or directory under the resource url
            # and if the resource_url which has been found is longer (and there
            #-fore more specific) than the last one, we save it as current best
            # match
            if resource_url in url and len(resource_url) > len(current_best_match):
                current_best_match = resource_url
        if current_best_match in self.resources:
            # this is just to check we did find something, it is possible we didn't
            return self.resources[current_best_match]
        else:
            self.sendServerError(404, 'Not Found')
            return None # this is how we know something has gone wrong

    def sendServerError(self, code, message):
        # this sends back a server error with the message given
        top_line = 'HTTP/%s %s %s' % (self.version, self.code, self.message)
        self.sendLine(top_line)
        self.transport.loseConnection()

    def createResponse(self):
        # Okay so here's how this is gonna work. We are going to assume this
        # is being called after a request has come in and the lines have been
        # parsed. It will go ahead and find the best match for the url. Then
        # if it finds a resource it will figure out if we have a post or get
        # request. If it is one of the two it will initialize a request with
        # the url, headers, and body found. Then it will call the appropriate
        # method on the resource and return the result (the result must be
        # a response object)
        resource = self.findBestMatch(self.url)
        if not resource:
            return None
        if self.method.upper() == 'GET':
            request = self.GET_request_object(self.url, self.headers, self.body)
            request.Process()
            response = resource.call_GET(request)   # if the call doesn't work
            # call_GET should return a response object with the appropriate
            # error code and the like
        elif self.method.upper() == 'POST':
            request = self.POST_request_object(self.url, self.headers, self.body)
            request.Process()
            response = resource.call_POST(request)   # if the call doesn't work
            # call_GET should return a response object with the appropriate
            # error code and the like
        else:
            self.sendServerError(405, 'Method Not Allowed')
            response = None # so that the next method knows not to try making
            # anything
        return response

    def sendResponse(self, response):
        # This works by taking a response object and the checking if it is
        # not none (if it is it just passes by), then it uses the information
        # coded in the response to write it out.
        if not response:
            return
        top_line = 'HTTP/%s %s %s' % (self.version, response.status, response.method)
        self.sendLine(top_line)
        for header in response.headers:
            header_line = '%s : ' % header
            for value in response.headers[header]:
                header_line = '%s%s, ' % (header_line, value)
            # shave the comma and the space
            header_line = header_line[:-2]
            self.sendLine(header_line)
        if response.body != '':
            self.sendLine('')
            self.transport.write(response.body)
        self.transport.loseConnection()

class Resource:

    def call_GET(self, request):
        # must return a response with the appropriate headers and such
        response = Response()
        response.status = 200
        response.message = 'OK'
        return response

    def call_POST(self, request):
        # must return a response with the appropriate headers and such
        response = Response()
        response.status = 200
        response.message = 'OK'
        return response
