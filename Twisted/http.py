# Python File http.py

import re

class Issue(Exception):
    def __init__(self, problem):
        self.problem = problem
    def __str__(self):
        return 'ERROR: the problem was: %s' % self.problem

class Status:

    codes = {100: 'Continue', 101: 'Switching Protocols', 102: 'Processing',
        103: 'Checkpoint', 200: 'OK', 201: 'Created', 202: 'Accepted',
        203: 'Non-Authoritative Information', 204: 'No Content', 205: 'Reset Content',
        206: 'Partial Content', 207: 'Multi-Status', 208: 'Already Reported',
        226: 'IM Used', 300: 'Multiple Choices', 301: 'Moved Permanently',
        302: 'Found', 303: 'See Other', 304: 'Not Modified', 305: 'Use Proxy',
        306: 'Switch Proxy', 307: 'Temporary Redirect', 308: 'Permanent Redirect',
        400: 'Bad Request', 401: 'Unauthorized', 402: 'Payment Required',
        403: 'Forbidden', 404: 'Not Found', 405: 'Method Not Allowed',
        406: 'Not Acceptable', 407: 'Proxy Authentication Required',
        408: 'Request Timeout', 409: 'Conflict', 410: 'Gone', 411: 'Length Required',
        412: 'Precondition Failed', 413: 'Payload Too Large',
        414: 'URI Too Long', 415: 'Unsupported Media Type', 416: 'Range Not Satisfiable',
        417: 'Expectation Failed', 418: "I'm a teapot", 419: 'Authentication Timeout',
        421: 'Misdirected Request', 422: 'Unprocessable Entity', 423: 'Locked',
        424: 'Failed Dependency', 426: 'Upgrade Required', 428: 'Precondition Required',
        431: 'Request Header Fields Too Large', 451: 'Unavailable For Legal Reasons',
        500: 'Internal Server Error', 501: 'Not Implemented', 502: 'Bad Gateway',
        503: 'Service Unavailable', 504: 'Gateway Timeout', 505: 'HTTP Version Not Supported',
        506: 'Variant Also Negotiates', 507: 'Insufficient Storage', 508: 'Loop Detected',
        510: 'Not Extended', 511: 'Network Authentication Required'}

    def __init__(self, code):
        code = int(code)    # someone might try inputting a string
        # we will initiate the two parts of status right here.
        # so all you have to do is input the code on initiation and bam you've
        # got it all and don't have to worry about what the message is
        self.code = code
        self.message = codes[code]

    def __str__(self):
        # I am going to have the string representation be that of a status
        # in the status line of an http response
        return '%s %s' % (self.code, self.message)

class Header:

    name = None
    values = []

    def __init__(self, name=None, value=None):
        # this way you can just setup a simple name: value
        # header during inititation to save lines of code
        self.name = name
        if value:
            self.values.append(value)

    def SetName(self, name):
        self.name = name

    def AddValue(self, value):
        self.values.append(value)

    def ParseLine(self, line):
        # we first compile the regular expression we are going to use in parsing
        # this line. You can see the form of header line we are expecting
        re_expression = re.compile('([\S]{1,})[\s]*:[\s]*([\s\S]*[\S])')
        # next we go ahead and try to find a match in the line that was given
        # we are only looking for one (and the first) match
        match = re.search(re_expression, line):
        # next we make sure we got a match if we didn't we don't want anything
        # besides throw an error
        if match:
            # the name will be in the first group
            self.name = match.group(1)
            # next we get the portion of the string which contains our values
            values_string = match.group(2)
            # we separate the string into the values by comma
            values = values.split(',')
            # now we are going to use the next few lines to get rid of
            # whitespace around the values
            cleaned_values = []
            for value in values:
                cleaned_values.append(value.strip())
            # and now we can set self.values
            self.values = cleaned_values
        else:
            raise Issue('No Header Line Match In Input Line: %s' % line)

    def WriteLine(self):
        # this method returns a line of the form: name: value1, value2, ...
        # first we will create the portion of the string that will containt the
        # values
        values_string = ''
        for value in self.values:
            values_string = '%s%s, ' % (values_string, value)
        # now we trim off the last comma and space
        values_string = values_string[:-2]
        # now we create the full string
        line = '%s: %s' % (self.name, values_string)
        # and we are done and can return the line :)
        return line

    def __str__(self):
        # the string representation will be that of a header line in an HTTP message
        return self.WriteLine()

class Url:
    
    self.scheme = None
    self.username = None
    self.password = None
    self.host = None
    self.port = None
    self.path = None
    self.query = None
    self.fragment = None

    def ParseLine(self, line):
        # first we compile the regular expression we are going to be using
        # groups:
        # 1 -> scheme 2 -> username 3 -> password 4 -> host 5 -> port
        # 6 -> path 7 -> query 8 -> fragment
        # built from  scheme:[//[user:password@]host[:port]][/]path[?query][#fragment]
        # and yeah it's pretty long... o_o
        re_expression = re.compile('(?:([a-zA-z0-9+\-.]{1,}):)?(?:\/\/(?:([a-zA-z0-9+\-.]{1,}):([a-zA-z0-9+\-.]{1,})@)?(?:([a-zA-z0-9+\-.]{1,})(?::([0-9]{1,}))?)?)?(\/?[a-zA-z0-9+\-.%\/]*)?(?:\?([^\s#]{1,}))?(?:#([\S]*))?')
        # next we try to get a match and we only want one and the first match from the line
        match = re.search(re_expression, line)
        # next we make sure we got a match
        if match:
            # now we can go ahead and match the various parts
            self.scheme = match.group(1)
            self.username = match.group(2)
            self.password = match.group(3)
            self.host = match.group(4)
            self.port = match.group(5)
            self.path = match.group(6)
            self.query = match.group(7)
            self.fragment = match.group(8)
        else:
            raise Issue('No Url Match In Input Line: %s' % line)
