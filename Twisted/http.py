# Python File http.py

import re

class Issue(Exception):
    def __init__(self, problem):
        self.problem = problem
    def __str__(self):
        return 'ERROR: the problem was: %s' % self.problem

class HTTPComponent:
    """
    This class embodies the idea that you shouldbe able to parse
    a line that comes from an http message that corresponds to this
    kind of object and setup the object from that line. That you should
    be able to write out a line from this object in the form that it
    would take in a http message. and that the string representation is
    exactly that line
    """

    def ParseLine(self, line):
        # you will have to write the functionality yourself
        # but the line be the corresponding string representing
        # the object in an http message. This should return nothing
        # and set all of the attributes in this object
        pass

    def WriteLine(self):
        # this should use the set attributes of this object to create
        # an http message string version of the object. It must return that
        # line
        return ''

    def __str__(self):
        # the string rep should be the http message version of this object
        return self.WriteLine()

class Status(HTTPComponent):

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

    def __init__(self, code=None):
        if not code:
            self.code = None
            self.message = None
            return
        code = int(code)    # someone might try inputting a string
        # we will initiate the two parts of status right here.
        # so all you have to do is input the code on initiation and bam you've
        # got it all and don't have to worry about what the message is
        if code in self.codes:
            self.code = code
            self.message = self.codes[code]
        else:
            raise Issue('Input Code %s Not Found In Codes' % code)

    def ParseLine(self, line):
        # first we compile the regular expression we will be using
        re_expression = re.compile('([1-5][0-9][0-9]) [a-zA-Z\-\'][\sa-zA-Z\-\']*')
        # now try for a single (and first) match
        match = re.search(re_expression, line)
        checkMatch(match, line, 'Version')
        # now that we are all good
        if int(match.group(1)) in self.codes:
            self.code = int(match.group(1))
            # now to be consistent we are going to set the message as the one
            # in codes corresponding to code
            self.message = self.codes[self.code]
        else:
            raise Issue('Unknown Code Found: %s (Input Line: %s)' % (match.group(1), line))

    def WriteLine(self):
        # I am going to have the string representation be that of a status
        # in the status line of an http response
        return '%s %s' % (self.code, self.message)

    def __eq__(self, other):
        if self.code == other.code and self.message == other.message:
            return True
        else:
            return False

class Header(HTTPComponent):

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
        match = re.search(re_expression, line)
        checkMatch(match, line, 'Header')
        # now that we are all good
        # the name will be in the first group
        self.name = match.group(1)
        # next we get the portion of the string which contains our values
        values_string = match.group(2)
        # we separate the string into the values by comma
        values = values_string.split(',')
        # now we are going to use the next few lines to get rid of
        # whitespace around the values
        cleaned_values = []
        for value in values:
            cleaned_values.append(value.strip())
        # and now we can set self.values
        self.values = cleaned_values

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

    def __eq__(self, other):
        if not self.name == other.name:
            return False
        # to make sure order of values doesn't matter
        for value in self.values:
            if not value in other.values:
                return False
        return True

class Url(HTTPComponent):

    scheme = None
    username = None
    password = None
    host = None
    port = None
    path = None
    query = None
    fragment = None

    # in each of the following set methods we are going to make sure
    # that each input in is the right form using regular expressions
    def SetScheme(self, scheme):
        re_expression = re.compile('[a-zA-z0-9+\-.]{1,}')
        match = re.search(re_expression, scheme)
        checkMatch(match, scheme, 'Scheme')
        # we are all good and so can set the attribute
        self.scheme = scheme

    def SetCredentials(self, username, password):
        # first we know that if we don't have a host yet, we cannot have this stuff
        # so first we check for a host
        if not self.host:
            raise Issue('No Credentials Can Be Added Until Host Has Been Set')
        # first for the username
        re_expression = re.compile('[a-zA-z0-9+\-.]{1,}')
        match = re.search(re_expression, username)
        checkMatch(match, username, 'Username')
        # now for the password
        match = re.search(re_expression, password)
        checkMatch(match, password, 'Password')
        # we are all good and so can set the attribute
        self.username = username
        self.password = password

    def SetHost(self, host):
        # first we know that if we don't have a scheme yet, we cannot have this stuff
        # so first we check for a scheme
        if not self.scheme:
            raise Issue('No Host Can Be Added Until Scheme Has Been Set')
        re_expression = re.compile('[a-zA-z0-9+\-.]{1,}')
        match = re.search(re_expression, host)
        checkMatch(match, host, 'Host')
        # we are all good and so can set the attribute
        self.host = host

    def SetPort(self, port):
        # port might be in int form so first we make in a string
        port = port.toString()
        # first we know that if we don't have a host yet, we cannot have this stuff
        # so first we check for a host
        if not self.host:
            raise Issue('No Port Can Be Added Until Host Has Been Set')
        re_expression = re.compile('[0-9]{1,}')
        match = re.search(re_expression, port)
        checkMatch(match, port, 'Port')
        # we are all good and so can set the attribute
        self.port = port

    def SetPath(self, path):
        re_expression = re.compile('\/?[a-zA-z0-9+\-.%][a-zA-z0-9+\-.%\/]*')
        match = re.search(re_expression, path)
        checkMatch(match, path, 'Path')
        # we are all good and so can set the attribute
        self.path = path

    def SetQuery(self, query):
        re_expression = re.compile('[^\s#]{1,}')
        match = re.search(re_expression, query)
        checkMatch(match, query, 'Query')
        # we are all good and so can set the attribute
        self.query = query

    def SetFragment(self, fragment):
        re_expression = re.compile('([\S]*)')
        match = re.search(re_expression, fragment)
        checkMatch(match, fragment, 'Fragment')
        # we are all good and so can set the attribute
        self.fragment = fragment

    def ParseLine(self, line):
        # first we compile the regular expression we are going to be using
        # groups:
        # 1 -> scheme 2 -> username 3 -> password 4 -> host 5 -> port
        # 6 -> path 7 -> query 8 -> fragment
        # built from  [scheme:][[//][username:password@]host[:port]][path][?query][#fragment]
        # we are assuming that if we have a host address we will have a scheme
        # and yeah it's pretty long... o_o
        re_expression = re.compile('(?:([a-zA-z0-9+\-.]{1,}):)?(?:\/\/(?:([a-zA-z0-9+\-.]{1,}):([a-zA-z0-9+\-.]{1,})@)?([a-zA-z0-9+\-.]{1,})(?::([0-9]{1,}))?)?(\/?[a-zA-z0-9+\-.%][a-zA-z0-9+\-.%\/]*)?(?:\?([^\s#]{1,}))?(?:#([\S]*))?')
        # next we try to get a match and we only want one and the first match from the line
        match = re.search(re_expression, line)
        checkMatch(match, line, 'Url')
        # now that we are all good
        # now we can go ahead and get the various parts
        self.scheme = match.group(1)
        self.username = match.group(2)
        self.password = match.group(3)
        self.host = match.group(4)
        self.port = match.group(5)
        self.path = match.group(6)
        self.query = match.group(7)
        self.fragment = match.group(8)
        # now we make sure that if we have a host we have a scheme
        if self.host and not self.scheme:
            raise Issue('Host Address %s requires a scheme. (Input Line: %s)' % (self.host, line))

    def WriteLine(self):
        # once again the form of a url is the following:
        # [scheme:][[//][username:password@]host[:port]][path][?query][#fragment]
        # we are assuming that if we have a host address we have a scheme
        # so let us move our way from left to right in building this
        line = ''
        if self.scheme:
            line = '%s:' % self.scheme
            # remember if we have a host we must have a scheme
            if self.host:
                line = '%s//' % line
            if self.username:
                line = '%s%s:%s@' % (line, self.username, self.password)
            line = '%s%s' % (line, self.host)
            if self.port:
                line = '%s:%s' % (line, self.port)
        if self.path:
            line = '%s%s' % (line, self.path)
        if self.query:
            line = '%s?%s' % (line, self.query)
        if self.fragment:
            line = '%s#%s' % (line, self.fragment)
        # and now we are done and can return the line! :D
        return line

    def __eq__(self, other):
        if self.scheme != other.scheme:
            return False
        if self.host != other.host:
            return False
        if self.username != other.username:
            return False
        if self.password != other.password:
            return False
        if self.port != other.port:
            return False
        if self.path != other.path:
            return False
        if self.query != other.query:
            return False
        if self.fragment != other.fragment:
            return False
        return True


"""
So a version is more than just a number. It is essentially an object that let's
us know (in theory) which headers to use, how to use them, restrictions on messages,
etc. So I am going to create a Version object here, so that I can expand it later
if needed.

For the first go though, it is just going to have the version number and print
itself like in a message
"""

class Version(HTTPComponent):

    def __init__(self, number='1.1'):
        # just to make sure it is a string
        number = str(number)
        # now we make sure it is the right form
        re_expression = re.compile('[0-9].[0-9]{1,}')
        match = re.search(re_expression, number)
        checkMatch(match, number, 'Version Number')
        # now that we know we are all good we go ahead and set the number
        self.number = number

    def ParseLine(self, line):
        # first we compile the regular expression we are going to use
        re_expression = re.compile('HTTP\/([0-9]\.[0-9]{1,})')
        # next we try for a match, and we want one and the first
        match = re.search(re_expression, line)
        checkMatch(match, line, 'Version')
        # now that we are all good
        # we set the number
        self.number = match.group(1)

    def WriteLine(self):
        # this is really simple
        line = 'HTTP/%s' % self.number
        return line

    def __eq__(self, other):
        if self.number != other.number:
            return False
        return True

class Method(HTTPComponent):
    """
    One method has several string representations, therefore it is a bit
    more than its representations, so we will create an additional object
    for it.
    """

    methods = ['OPTIONS', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'TRACE', 'CONNECT']

    def __init__(self, method=None):
        if not method:
            self.method = None
            return
        if method.upper() in self.methods:
            self.method = method.upper()
        else:
            raise Issue('Input Method %s Is Not a Valid Method' % method)

    def ParseLine(self, line):
        # first we have our regular expression
        re_expression = re.compile('[a-zA-Z]{1,}')
        match = re.search(re_expression, line)
        checkMatch(match, line, 'Method')
        # now that we know we have only one word
        # we essentially just throw our line to uppercase and see if it is in our
        # methods list
        upper_line = line.upper()
        if upper_line in self.methods:
            self.method = upper_line
        else:
            raise Issue('No Method Was Found In Input Line: %s' % line)

    def WriteLine(self):
        # this is super easy
        line = self.method
        return line

    def __eq__(self, other):
        if self.method != other.method:
            return False
        return True

"""
GENERAL FUNCTIONS
"""

def checkMatch(match, input, input_name):
    # this method will raise an error if somethign is wrong with the match
    # input name is the name used to refer to the input in the error messages
    # it makes sure the match exists and is equal to input
    if match:
        # we want to make sure that the whole expression is this match
        # otherwise we are going to need to raise an issue
        if not match.group(0) == input:
            raise Issue('%s Match In Input Is Only Part Of Input: %s' % (input_name, input))
    else:
        raise Issue('No %s Match Found In Input: %s' % (input_name, input))
