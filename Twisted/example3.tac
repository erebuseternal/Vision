# example 3

from twisted.web.server import Site
from twisted.application import internet, service
from twisted.web.resource import Resource, NoResource

from calendar import calendar

class YearPage(Resource):
    def __init__(self, year):
        Resource.__init__(self)
        self.year = year

    def render_GET(self, request):
        return "<html><body><pre>%s</pre></body></html>" % (calendar(self.year),)

class CalendarHome(Resource):
    def getChild(self, name, request):
        if name == '':
            return self
        if name.isdigit():
            return YearPage(int(name))
        else:
            return NoResource()

    def render_GET(self, request):
        return "<html><body>Welcome to the calendar server!</body></html>"

root = CalendarHome()
factory = Site(root)
application = service.Application('dynamic')
staticService = internet.TCPServer(80, factory)
staticService.setServiceParent(application)
