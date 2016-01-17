# Python File isaac.py

"""
We need an HTTP server for the IdeaBazaar. First there is input, both
through cookies and a url. This the gets parsed and entered into a inputhandler.
Then the handler will do some 'magick' and then act as a dictionary with a set
of fields as keys and the values as the values those fields have given the
input data. Then we use the joinData function from fieldextractor to combine
this with a dynamic HTML page attached to the resource. This final page is
then returned to the user.

The steps then are the following:
    * grab two parts of the url:
        * the part having to do with which page to choose
        * the part having information to input to the handler
    * grab the input from the cookie
    * send all of this to the input handler and then call a Grab method on the
        input handler
    * then we join using joinData and a FieldMarker and the input handler
    * finally we grab any cookie info from the handler that needs to be kept

So how will we separate the url into its two pieces?
"""

from twisted.protocols import basic
from twisted.internet import protcol, reactor
import re

class Isaac(basic.lineReceiver):
    method = None
    url = None
    headers = {}
    body = []

    def __init__(self):
        self.lines = []
        self.request_line_expression = re.compile('(?i)([\S]{1,})[\s]{1,}([\S]{1,})[\s]{1,}HTTP\/([\S]{1,})')
        self.header_line_expression = re.compile('([\S]{1,})[\s]*:[\s]*([\s\S]*[\S])')
        self.line_parser = self.request_lineParser
        self.parsed_request_line = False

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
        # we've come to the end. Time to resent and call the method to create
        # and send the response
        if not line:
            self.parsed_request_line = False
            self.line_parser = self.request_lineParser
            self.sendResponse()

    def sendResponse(self):
        # here is where we create the response
        pass

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
        line.strip()
        self.body.append(line)
