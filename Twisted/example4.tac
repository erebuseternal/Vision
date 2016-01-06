# example 4
from twisted.web.server import Site
from twisted.application import internet, service
from twisted.web.resource import Resource
import cgi

class FormPage(Resource):
    isLeaf = True
    def render_GET(self, request):
        return """
        <html>
        <body>
        <form method="POST">
        <input name="form-field" type="text" />
        <input type="submit" />
        </form>
        </body>
        </html>
        """
    def render_POST(self, request):
        return """
        <html>
        <body>You submitted: %s</body>
        </html>
        """ % (cgi.escape(request.args["form-field"][0]),)

factory = Site(FormPage())
application = service.Application('static3')
staticService = internet.TCPServer(80, factory)
staticService.setServiceParent(application)
