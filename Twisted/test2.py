from http import *

request_lines = []
request_lines.append('POST \hello.html  HTTP/1.2')
request_lines.append('Header: Value')
request_lines.append('Howdy: how, are, you')
request_lines.append('')
request_lines.append('body this is the body')
request_lines.append('and this is the second line')
request_lines.append(None)

request = Request()
for line in request_lines:
    request.ParseLine(line)

print(request)

request.Parse(request.Write())
print(request)

response_lines = []
response_lines.append('HTTP/1.2 200 OK')
response_lines.append('Header: Value')
response_lines.append('Howdy: how, are, you')
response_lines.append('')
response_lines.append('body this is the body')
response_lines.append('and this is the second line')

response = Response()
for line in response_lines:
    response.ParseLine(line)

print(response)
